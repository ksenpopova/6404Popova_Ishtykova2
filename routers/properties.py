from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db
from security import get_current_user, require_agent

router = APIRouter()

@router.post("/", response_model=schemas.InsuredPropertyOut, status_code=201)
def create_property(prop: schemas.InsuredPropertyCreate, db: Session = Depends(get_db),
                    user: models.User = Depends(require_agent)):
    db_prop = models.InsuredProperty(**prop.model_dump())
    db.add(db_prop)
    db.commit()
    db.refresh(db_prop)
    return db_prop

@router.get("/", response_model=List[schemas.InsuredPropertyOut])
def get_properties(db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    return db.query(models.InsuredProperty).all()


@router.get("/{property_id}", response_model=schemas.InsuredPropertyOut)
def get_property(property_id: int, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    prop = db.get(models.InsuredProperty, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Имущество не найдено")
    return prop


@router.put("/{property_id}", response_model=schemas.InsuredPropertyOut)
def update_property(property_id: int, data: schemas.InsuredPropertyCreate, db: Session = Depends(get_db),
                    user: models.User = Depends(require_agent)):
    prop = db.get(models.InsuredProperty, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Имущество не найдено")
    for key, value in data.model_dump().items():
        setattr(prop, key, value)
    db.commit()
    db.refresh(prop)
    return prop


@router.delete("/{property_id}", status_code=204)
def delete_property(property_id: int, db: Session = Depends(get_db),
                    user: models.User = Depends(require_agent)):
    prop = db.get(models.InsuredProperty, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Имущество не найдено")
    if db.query(models.contract_property_link).filter_by(property_id=property_id).first():
        raise HTTPException(status_code=409, detail="Имущество используется в договоре")
    db.delete(prop)
    db.commit()
