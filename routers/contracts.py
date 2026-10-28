from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db

router = APIRouter()


@router.post("/", response_model=schemas.InsuranceContractOut, status_code=201)
def create_contract(contract: schemas.InsuranceContractCreate, db: Session = Depends(get_db)):
    # Извлекаем все данные, кроме списка ID имущества
    contract_data = contract.model_dump(exclude={"property_ids"})

    # Проверяем существование связанных ключей (клиент, агент, продукт)
    if not db.query(models.Client).filter(models.Client.id == contract.client_id).first():
        raise HTTPException(status_code=404, detail="Клиент не найден")

    db_contract = models.InsuranceContract(**contract_data)

    # Обработка связи N:M (Многие-ко-многим)
    if contract.property_ids:
        # Ищем имущество по переданным ID
        properties = db.query(models.InsuredProperty).filter(
            models.InsuredProperty.id.in_(contract.property_ids)
        ).all()

        if len(properties) != len(contract.property_ids):
            raise HTTPException(status_code=404, detail="Одно или несколько указанных имуществ не найдено")

        # Добавляем найденное имущество в отношение (название переменной 'properties' должно совпадать с relationship в models.py)
        db_contract.properties.extend(properties)

    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract


@router.get("/{contract_id}", response_model=schemas.InsuranceContractOut)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(models.InsuranceContract).filter(models.InsuranceContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    return contract