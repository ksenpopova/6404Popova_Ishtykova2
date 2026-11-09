from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db
from security import require_agent

router = APIRouter()

@router.post("/", response_model=schemas.AgentOut, status_code=201)
def create_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db),
                 user: models.User = Depends(require_agent)):
    db_agent = models.Agent(**agent.model_dump())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.get("/", response_model=List[schemas.AgentOut])
def get_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               user: models.User = Depends(require_agent)):
    return db.query(models.Agent).offset(skip).limit(limit).all()

@router.get("/{agent_id}", response_model=schemas.AgentOut)
def get_agent(agent_id: int, db: Session = Depends(get_db),
              user: models.User = Depends(require_agent)):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Агент не найден")
    return agent


@router.put("/{agent_id}", response_model=schemas.AgentOut)
def update_agent(agent_id: int, data: schemas.AgentCreate, db: Session = Depends(get_db),
                 user: models.User = Depends(require_agent)):
    agent = db.get(models.Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Агент не найден")
    for key, value in data.model_dump().items():
        setattr(agent, key, value)
    db.commit()
    db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
def delete_agent(agent_id: int, db: Session = Depends(get_db),
                 user: models.User = Depends(require_agent)):
    agent = db.get(models.Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Агент не найден")
    if agent.contracts or db.query(models.UserProfile).filter_by(agent_id=agent_id).first():
        raise HTTPException(status_code=409, detail="Агент связан с договором или учётной записью")
    db.delete(agent)
    db.commit()
