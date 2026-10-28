from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.InsuredPropertyOut, status_code=201)
def create_property(prop: schemas.InsuredPropertyCreate, db: Session = Depends(get_db)):
    db_prop = models.InsuredProperty(**prop.model_dump())
    db.add(db_prop)
    db.commit()
    db.refresh(db_prop)
    return db_prop

@router.get("/", response_model=List[schemas.InsuredPropertyOut])
def get_properties(db: Session = Depends(get_db)):
    return db.query(models.InsuredProperty).all()