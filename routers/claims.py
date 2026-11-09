from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime, timezone

import models, schemas
from database import get_db
from security import get_current_user, require_agent

router = APIRouter()


@router.post("/", response_model=schemas.ClaimOut, status_code=201)
def create_claim(claim: schemas.ClaimCreate, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    # Проверка бизнес-логики: существует ли договор, по которому заявляют убыток
    contract = db.query(models.InsuranceContract).filter(models.InsuranceContract.id == claim.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    if user.profile.role == "client" and contract.client_id != user.profile.client_id:
        raise HTTPException(status_code=403, detail="Доступ к чужому договору запрещён")

    status = db.query(models.ClaimStatus).filter_by(status_name="Новая").first()
    if not status:
        status = models.ClaimStatus(status_name="Новая")
        db.add(status)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            status = db.query(models.ClaimStatus).filter_by(status_name="Новая").one()

    db_claim = models.InsuranceClaim(
        contract_id=claim.contract_id,
        description=claim.description,
        amount_of_damage=claim.amount_of_damage,
        status_id=status.id,
        incident_time=claim.incident_time or datetime.now(timezone.utc).replace(tzinfo=None)
    )

    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim


@router.get("/statuses", response_model=List[schemas.ClaimStatusOut])
def get_statuses(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.ClaimStatus).order_by(models.ClaimStatus.id).all()


@router.get("/statuses/{status_id}", response_model=schemas.ClaimStatusOut)
def get_status(status_id: int, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    item = db.get(models.ClaimStatus, status_id)
    if not item:
        raise HTTPException(status_code=404, detail="Статус не найден")
    return item


@router.post("/statuses", response_model=schemas.ClaimStatusOut, status_code=201)
def create_status(data: schemas.ClaimStatusBase, db: Session = Depends(get_db),
                  user: models.User = Depends(require_agent)):
    if db.query(models.ClaimStatus).filter_by(status_name=data.status_name).first():
        raise HTTPException(status_code=409, detail="Статус уже существует")
    item = models.ClaimStatus(**data.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Статус уже существует") from exc
    db.refresh(item)
    return item


@router.put("/statuses/{status_id}", response_model=schemas.ClaimStatusOut)
def update_status(status_id: int, data: schemas.ClaimStatusBase, db: Session = Depends(get_db),
                  user: models.User = Depends(require_agent)):
    item = db.get(models.ClaimStatus, status_id)
    if not item:
        raise HTTPException(status_code=404, detail="Статус не найден")
    if db.query(models.ClaimStatus).filter(models.ClaimStatus.status_name == data.status_name,
                                           models.ClaimStatus.id != status_id).first():
        raise HTTPException(status_code=409, detail="Статус уже существует")
    item.status_name = data.status_name
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Статус уже существует") from exc
    db.refresh(item)
    return item


@router.delete("/statuses/{status_id}", status_code=204)
def delete_status(status_id: int, db: Session = Depends(get_db),
                  user: models.User = Depends(require_agent)):
    item = db.get(models.ClaimStatus, status_id)
    if not item:
        raise HTTPException(status_code=404, detail="Статус не найден")
    if item.claims:
        raise HTTPException(status_code=409, detail="Статус используется в заявках")
    db.delete(item)
    db.commit()


@router.get("/", response_model=List[schemas.ClaimOut])
def get_claims(skip: int = 0, limit: int = 100, status_id: int | None = None,
               db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    query = db.query(models.InsuranceClaim)
    if user.profile.role == "client":
        query = query.join(models.InsuranceContract).filter(
            models.InsuranceContract.client_id == user.profile.client_id)
    if status_id is not None:
        query = query.filter(models.InsuranceClaim.status_id == status_id)
    return query.offset(skip).limit(limit).all()


@router.get("/{claim_id}", response_model=schemas.ClaimOut)
def get_claim(claim_id: int, db: Session = Depends(get_db),
              user: models.User = Depends(get_current_user)):
    claim = db.query(models.InsuranceClaim).filter(models.InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Страховой случай не найден")
    if user.profile.role == "client" and claim.contract.client_id != user.profile.client_id:
        raise HTTPException(status_code=403, detail="Доступ к чужой заявке запрещён")
    return claim


@router.patch("/{claim_id}", response_model=schemas.ClaimOut)
def update_claim(claim_id: int, data: schemas.ClaimUpdate, db: Session = Depends(get_db),
                 user: models.User = Depends(require_agent)):
    claim = db.get(models.InsuranceClaim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Страховой случай не найден")
    changes = data.model_dump(exclude_unset=True)
    if "status_id" in changes and not db.get(models.ClaimStatus, changes["status_id"]):
        raise HTTPException(status_code=404, detail="Статус не найден")
    for key, value in changes.items():
        setattr(claim, key, value)
    db.commit()
    db.refresh(claim)
    return claim


@router.delete("/{claim_id}", status_code=204)
def delete_claim(claim_id: int, db: Session = Depends(get_db),
                 user: models.User = Depends(require_agent)):
    claim = db.get(models.InsuranceClaim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Страховой случай не найден")
    db.delete(claim)
    db.commit()
