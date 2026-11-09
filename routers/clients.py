from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import IntegrityError

import models, schemas
from database import get_db
from security import get_current_user, require_agent

router = APIRouter()

@router.post("/", response_model=schemas.ClientOut, status_code=201)
def create_client(
    client: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_agent)
):
    db_client = models.Client(**client.model_dump())
    db.add(db_client)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Паспорт уже используется") from exc
    db.refresh(db_client)
    return db_client

@router.get("/", response_model=List[schemas.ClientOut])
def get_clients(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Client)
    if current_user.profile.role == "client":
        query = query.filter(models.Client.id == current_user.profile.client_id)
    return query.offset(skip).limit(limit).all()

@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    if current_user.profile.role == "client" and current_user.profile.client_id != client_id:
        raise HTTPException(status_code=403, detail="Доступ к чужому профилю запрещён")
    return client


@router.put("/{client_id}", response_model=schemas.ClientOut)
def update_client(client_id: int, data: schemas.ClientCreate, db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    if user.profile.role != "agent" and user.profile.client_id != client_id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    for key, value in data.model_dump().items():
        setattr(client, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Паспорт уже используется") from exc
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db),
                  user: models.User = Depends(require_agent)):
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    if client.contracts or db.query(models.UserProfile).filter_by(client_id=client_id).first():
        raise HTTPException(status_code=409, detail="Клиент связан с договором или учётной записью")
    db.delete(client)
    db.commit()
