from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
import models, schemas

router = APIRouter(prefix="/claims", tags=["Claims"])

@router.get("/", response_model=list[schemas.ClaimOut])
def get_all_claims(db: Session = Depends(get_db)):
    return db.query(models.InsuranceClaim).all()

@router.post("/", response_model=schemas.ClaimOut, status_code=201)
def create_claim(claim: schemas.ClaimCreate, db: Session = Depends(get_db)):
    # Проверяем, существует ли контракт
    contract = db.query(models.InsuranceContract).filter(models.InsuranceContract.id == claim.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")

    # Ищем статус "Новая" по умолчанию
    status_new = db.query(models.ClaimStatus).filter(models.ClaimStatus.status_name == "Новая").first()
    status_id = status_new.id if status_new else 1

    db_claim = models.InsuranceClaim(
        contract_id=claim.contract_id,
        description=claim.description,
        amount_of_damage=claim.amount_of_damage,
        status_id=status_id,
        incident_time=datetime.now()
    )
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim