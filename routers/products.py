from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db
from security import get_current_user, require_agent

router = APIRouter()

@router.post("/", response_model=schemas.InsuranceProductOut, status_code=201)
def create_product(product: schemas.InsuranceProductBase, db: Session = Depends(get_db),
                   user: models.User = Depends(require_agent)):
    db_product = models.InsuranceProduct(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/", response_model=List[schemas.InsuranceProductOut])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    return db.query(models.InsuranceProduct).offset(skip).limit(limit).all()


@router.get("/{product_id}", response_model=schemas.InsuranceProductOut)
def get_product(product_id: int, db: Session = Depends(get_db),
                user: models.User = Depends(get_current_user)):
    product = db.get(models.InsuranceProduct, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    return product


@router.put("/{product_id}", response_model=schemas.InsuranceProductOut)
def update_product(product_id: int, data: schemas.InsuranceProductBase, db: Session = Depends(get_db),
                   user: models.User = Depends(require_agent)):
    product = db.get(models.InsuranceProduct, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    for key, value in data.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db),
                   user: models.User = Depends(require_agent)):
    product = db.get(models.InsuranceProduct, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    if product.contracts:
        raise HTTPException(status_code=409, detail="Продукт используется в договоре")
    db.delete(product)
    db.commit()
