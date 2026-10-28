from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/", response_model=list[schemas.ClientOut])
def get_all_clients(db: Session = Depends(get_db)):
    # Чтение всех клиентов из БД
    clients = db.query(models.Client).all()
    return clients

@router.post("/", response_model=schemas.ClientOut, status_code=201)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    # Распаковываем проверенные Pydantic-данные в SQLAlchemy-модель
    db_client = models.Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client) # Обновляем объект, чтобы получить сгенерированный ID
    return db_client

@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client