from fastapi import APIRouter, HTTPException
import schemas

router = APIRouter()

@router.post("/login")
def login(user: schemas.UserAuth):
    if user.username == "admin" and user.password == "admin":
        return {"message": "Успешная авторизация", "token": "fake-jwt-token"}
    raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")