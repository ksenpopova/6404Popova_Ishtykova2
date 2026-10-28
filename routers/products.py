from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.InsuranceProductOut, status_code=201)
def create_product(product: schemas.InsuranceProductBase, db: Session = Depends(get_db)):
    db_product = models.InsuranceProduct(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/", response_model=List[schemas.InsuranceProductOut])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.InsuranceProduct).offset(skip).limit(limit).all()