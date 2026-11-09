from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db
from security import get_current_user, require_agent

router = APIRouter()


@router.post("/", response_model=schemas.InsuranceContractOut, status_code=201)
def create_contract(contract: schemas.InsuranceContractCreate, db: Session = Depends(get_db),
                    user: models.User = Depends(require_agent)):
    # Извлекаем все данные, кроме списка ID имущества
    contract_data = contract.model_dump(exclude={"property_ids"})

    # Проверяем существование связанных ключей (клиент, агент, продукт)
    if not db.query(models.Client).filter(models.Client.id == contract.client_id).first():
        raise HTTPException(status_code=404, detail="Клиент не найден")
    if not db.get(models.Agent, contract.agent_id):
        raise HTTPException(status_code=404, detail="Агент не найден")
    if not db.get(models.InsuranceProduct, contract.product_id):
        raise HTTPException(status_code=404, detail="Продукт не найден")

    db_contract = models.InsuranceContract(**contract_data)

    # Обработка связи N:M (Многие-ко-многим)
    if contract.property_ids:
        # Ищем имущество по переданным ID
        properties = db.query(models.InsuredProperty).filter(
            models.InsuredProperty.id.in_(contract.property_ids)
        ).all()

        if len(properties) != len(set(contract.property_ids)):
            raise HTTPException(status_code=404, detail="Одно или несколько указанных имуществ не найдено")

        # Добавляем найденное имущество в отношение (название переменной 'properties' должно совпадать с relationship в models.py)
        db_contract.properties.extend(properties)

    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract


@router.get("/", response_model=List[schemas.InsuranceContractOut])
def get_contracts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    query = db.query(models.InsuranceContract)
    if user.profile.role == "client":
        query = query.filter(models.InsuranceContract.client_id == user.profile.client_id)
    return query.offset(skip).limit(limit).all()


@router.get("/{contract_id}", response_model=schemas.InsuranceContractOut)
def get_contract(contract_id: int, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    contract = db.query(models.InsuranceContract).filter(models.InsuranceContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    if user.profile.role == "client" and contract.client_id != user.profile.client_id:
        raise HTTPException(status_code=403, detail="Доступ к чужому договору запрещён")
    return contract


@router.put("/{contract_id}", response_model=schemas.InsuranceContractOut)
def update_contract(contract_id: int, data: schemas.InsuranceContractUpdate,
                    db: Session = Depends(get_db), user: models.User = Depends(require_agent)):
    contract = db.get(models.InsuranceContract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    if not db.get(models.Client, data.client_id) or not db.get(models.Agent, data.agent_id) or not db.get(models.InsuranceProduct, data.product_id):
        raise HTTPException(status_code=404, detail="Клиент, агент или продукт не найден")
    properties = db.query(models.InsuredProperty).filter(models.InsuredProperty.id.in_(data.property_ids)).all()
    if len(properties) != len(set(data.property_ids)):
        raise HTTPException(status_code=404, detail="Имущество не найдено")
    for key, value in data.model_dump(exclude={"property_ids"}).items():
        setattr(contract, key, value)
    contract.properties = properties
    db.commit()
    db.refresh(contract)
    return contract


@router.delete("/{contract_id}", status_code=204)
def delete_contract(contract_id: int, db: Session = Depends(get_db),
                    user: models.User = Depends(require_agent)):
    contract = db.get(models.InsuranceContract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    if contract.claims:
        raise HTTPException(status_code=409, detail="Сначала удалите страховые случаи договора")
    contract.properties.clear()
    db.delete(contract)
    db.commit()
