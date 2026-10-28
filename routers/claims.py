from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

import models, schemas
from database import get_db

router = APIRouter()


@router.post("/", response_model=schemas.ClaimOut, status_code=201)
def create_claim(claim: schemas.ClaimCreate, db: Session = Depends(get_db)):
    # Проверка бизнес-логики: существует ли договор, по которому заявляют убыток
    contract = db.query(models.InsuranceContract).filter(models.InsuranceContract.id == claim.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")

    # Присваиваем статус по умолчанию (id=1)
    status = db.query(models.ClaimStatus).filter(models.ClaimStatus.id == 1).first()
    if not status:
        raise HTTPException(status_code=400, detail="В базе отсутствует базовый статус (id=1) для страхового случая")

    db_claim = models.InsuranceClaim(
        contract_id=claim.contract_id,
        description=claim.description,
        amount_of_damage=claim.amount_of_damage,
        status_id=status.id,
        incident_time=datetime.utcnow()
    )

    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim


@router.get("/", response_model=List[schemas.ClaimOut])
def get_claims(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.InsuranceClaim).offset(skip).limit(limit).all()


@router.get("/{claim_id}", response_model=schemas.ClaimOut)
def get_claim(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(models.InsuranceClaim).filter(models.InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Страховой случай не найден")
    return claim