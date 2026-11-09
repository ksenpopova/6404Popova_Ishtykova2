from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import hmac

import models, schemas
from database import get_db
from security import verify_password, get_password_hash, create_access_token

router = APIRouter()


@router.post("/register", response_model=schemas.UserOutAuth, status_code=201)
def register(user: schemas.UserCreateAuth, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Логин уже существует")

    if user.role == "agent":
        expected = os.getenv("AGENT_REGISTRATION_CODE")
        if not expected or not user.agent_code or not hmac.compare_digest(user.agent_code, expected):
            raise HTTPException(status_code=403, detail="Неверный код регистрации агента")

    try:
        hashed_pw = get_password_hash(user.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    new_user = models.User(username=user.username, hashed_password=hashed_pw)
    profile = models.UserProfile(role=user.role)
    try:
        if user.role == "client":
            client = models.Client(**user.client.model_dump())
            db.add(client)
            db.flush()
            profile.client_id = client.id
        else:
            agent = models.Agent(**user.agent.model_dump())
            db.add(agent)
            db.flush()
            profile.agent_id = agent.id
        new_user.profile = profile
        db.add(new_user)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Логин или паспорт уже используется") from exc
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "role": profile.role}


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not user.profile or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
