from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, TIMESTAMP, Table
from sqlalchemy.orm import relationship
from database import Base

# Связующая таблица для отношения N:M между договорами и имуществом[cite: 4]
contract_property_link = Table(
    'contract_property_link',
    Base.metadata,
    Column('contract_id', Integer, ForeignKey('insurance_contract.id'), primary_key=True),
    Column('property_id', Integer, ForeignKey('insured_property.id'), primary_key=True)
)


class Client(Base):
    __tablename__ = 'client'
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date)
    passport_info = Column(String, unique=True, index=True)
    contact_phone = Column(String)

    contracts = relationship("InsuranceContract", back_populates="client")


class Agent(Base):
    __tablename__ = 'agent'
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    position = Column(String)
    department = Column(String)

    contracts = relationship("InsuranceContract", back_populates="agent")


class InsuranceProduct(Base):
    __tablename__ = 'insurance_product'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type_of_insurance = Column(String)
    basic_tariff = Column(Numeric(10, 2))

    contracts = relationship("InsuranceContract", back_populates="product")


class ClaimStatus(Base):
    __tablename__ = 'claim_status'
    id = Column(Integer, primary_key=True, index=True)
    status_name = Column(String, unique=True, nullable=False)

    claims = relationship("InsuranceClaim", back_populates="status")


class InsuredProperty(Base):
    __tablename__ = 'insured_property'
    id = Column(Integer, primary_key=True, index=True)
    property_type = Column(String)
    market_value = Column(Numeric(15, 2))
    description = Column(Text)


class InsuranceContract(Base):
    __tablename__ = 'insurance_contract'
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('client.id'))
    agent_id = Column(Integer, ForeignKey('agent.id'))
    product_id = Column(Integer, ForeignKey('insurance_product.id'))
    contract_date = Column(Date)
    insurance_sum = Column(Numeric(15, 2))
    special_conditions = Column(Text)

    client = relationship("Client", back_populates="contracts")
    agent = relationship("Agent", back_populates="contracts")
    product = relationship("InsuranceProduct", back_populates="contracts")
    claims = relationship("InsuranceClaim", back_populates="contract")

    # Отношение N:M с имуществом[cite: 4]
    properties = relationship("InsuredProperty", secondary=contract_property_link)


class InsuranceClaim(Base):
    __tablename__ = 'insurance_claim'
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey('insurance_contract.id'))
    status_id = Column(Integer, ForeignKey('claim_status.id'))
    incident_time = Column(TIMESTAMP)
    description = Column(Text)
    amount_of_damage = Column(Numeric(15, 2))

    contract = relationship("InsuranceContract", back_populates="claims")
    status = relationship("ClaimStatus", back_populates="claims")