from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List


# --- Базовые справочники ---

class ClaimStatusBase(BaseModel):
    status_name: str


class ClaimStatusOut(ClaimStatusBase):
    id: int
    model_config = {"from_attributes": True}


class InsuranceProductBase(BaseModel):
    name: str
    type_of_insurance: str
    basic_tariff: float


class InsuranceProductOut(InsuranceProductBase):
    id: int
    model_config = {"from_attributes": True}


# --- Агенты ---

class AgentBase(BaseModel):
    full_name: str
    position: str
    department: str


class AgentCreate(AgentBase):
    pass


class AgentOut(AgentBase):
    id: int
    model_config = {"from_attributes": True}


# --- Клиенты ---

class ClientBase(BaseModel):
    full_name: str = Field(..., title="ФИО клиента")
    date_of_birth: date
    passport_info: str
    contact_phone: str


class ClientCreate(ClientBase):
    pass


class ClientOut(ClientBase):
    id: int
    model_config = {"from_attributes": True}


# --- Имущество ---

class InsuredPropertyBase(BaseModel):
    property_type: str
    market_value: float
    description: str


class InsuredPropertyCreate(InsuredPropertyBase):
    pass


class InsuredPropertyOut(InsuredPropertyBase):
    id: int
    model_config = {"from_attributes": True}


# --- Договоры (со связью N:M) ---

class InsuranceContractBase(BaseModel):
    client_id: int
    agent_id: int
    product_id: int
    contract_date: date
    insurance_sum: float
    special_conditions: Optional[str] = None


class InsuranceContractCreate(InsuranceContractBase):
    # При создании договора можно передать список ID имущества
    property_ids: List[int] = []


class InsuranceContractOut(InsuranceContractBase):
    id: int
    # Вложенная схема: при запросе договора API сразу отдаст список привязанного имущества
    properties: List[InsuredPropertyOut] = []

    model_config = {"from_attributes": True}


# --- Страховые случаи ---
class ClaimBase(BaseModel):
    contract_id: int
    description: str
    amount_of_damage: float


class ClaimCreate(ClaimBase):
    pass


class ClaimOut(ClaimBase):
    id: int
    status_id: int
    incident_time: datetime
    # Вложенная схема: возвращает связанный объект статуса целиком
    status: ClaimStatusOut

    model_config = {"from_attributes": True}


# --- Авторизация ---
class UserAuth(BaseModel):
    username: str
    password: str