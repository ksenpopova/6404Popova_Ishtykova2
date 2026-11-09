from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, Literal
from pydantic import model_validator


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
    property_ids: List[int] = Field(default_factory=list)


class InsuranceContractUpdate(InsuranceContractCreate):
    pass


class InsuranceContractOut(InsuranceContractBase):
    id: int
    # Вложенная схема: при запросе договора API сразу отдаст список привязанного имущества
    properties: List[InsuredPropertyOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# --- Страховые случаи ---
class ClaimBase(BaseModel):
    contract_id: int
    description: str
    amount_of_damage: float


class ClaimCreate(ClaimBase):
    incident_time: Optional[datetime] = None


class ClaimUpdate(BaseModel):
    description: Optional[str] = None
    amount_of_damage: Optional[float] = None
    status_id: Optional[int] = None


class ClaimOut(ClaimBase):
    id: int
    status_id: int
    incident_time: datetime
    # Вложенная схема: возвращает связанный объект статуса целиком
    status: ClaimStatusOut

    model_config = {"from_attributes": True}


# --- Авторизация ---
class UserCreateAuth(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    role: Literal["client", "agent"] = "client"
    client: Optional[ClientCreate] = None
    agent: Optional[AgentCreate] = None
    agent_code: Optional[str] = None

    @model_validator(mode="after")
    def check_profile(self):
        if self.role == "client" and (self.client is None or self.agent is not None):
            raise ValueError("Для роли client нужны данные client")
        if self.role == "agent" and (self.agent is None or self.client is not None):
            raise ValueError("Для роли agent нужны данные agent")
        return self

class UserOutAuth(BaseModel):
    id: int
    username: str
    role: str
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str
