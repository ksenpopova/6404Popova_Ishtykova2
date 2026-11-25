import logging
from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import uuid4

import grpc
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import get_db
from recommendations import recommendations_pb2 as messages
from recommendations.client import get_recommendation_client
from recommendations.recommendations_pb2_grpc import RecommendationServiceStub
from security import get_current_user

router = APIRouter()
logger = logging.getLogger("uvicorn.error").getChild("recommendations")


class RecommendationOut(BaseModel):
    product_id: int
    name: str
    insurance_type: str
    basic_tariff: Decimal
    matching_contracts: int
    latest_matching_contract_date: date | None


class RecommendationsOut(BaseModel):
    client_id: int
    items: list[RecommendationOut]


@router.get("/{client_id}/recommendations", response_model=RecommendationsOut)
def get_recommendations(
    client_id: Annotated[int, Path(gt=0, le=2**31 - 1)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[models.User, Depends(get_current_user)],
    client: Annotated[RecommendationServiceStub, Depends(get_recommendation_client)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
):
    if user.profile.role == "client" and user.profile.client_id != client_id:
        raise HTTPException(status_code=403, detail="Доступ к чужому профилю запрещён")
    if db.get(models.Client, client_id) is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    contract = models.InsuranceContract
    product = models.InsuranceProduct
    history = db.execute(
        select(contract.product_id, product.type_of_insurance, contract.contract_date)
        .outerjoin(product, contract.product_id == product.id)
        .where(contract.client_id == client_id, contract.product_id.is_not(None))
    )
    catalog = db.execute(select(product.id, product.name, product.type_of_insurance, product.basic_tariff))
    request = messages.RecommendRequest(
        history=[
            messages.ContractHistory(
                product_id=product_id,
                insurance_type=insurance_type or "",
                contract_date=contract_date.isoformat() if contract_date else None,
            )
            for product_id, insurance_type, contract_date in history
        ],
        catalog=[
            messages.Product(
                product_id=product_id,
                name=name,
                insurance_type=insurance_type or "",
                tariff_basis_points=int(tariff.scaleb(2)),
            )
            for product_id, name, insurance_type, tariff in catalog
            if tariff is not None and tariff.is_finite() and tariff >= 0
        ],
        limit=limit,
    )

    request_id = uuid4().hex
    logger.info("[%s] Calling Recommend for client_id=%d", request_id, client_id)
    try:
        result = client.Recommend(request, timeout=3, metadata=(("x-request-id", request_id),))
    except grpc.RpcError as exc:
        code = exc.code()
        logger.warning("[%s] Recommend failed: %s", request_id, code)
        if code == grpc.StatusCode.UNAVAILABLE:
            raise HTTPException(status_code=503, detail="Сервис рекомендаций недоступен") from exc
        if code == grpc.StatusCode.DEADLINE_EXCEEDED:
            raise HTTPException(status_code=504, detail="Сервис рекомендаций не ответил вовремя") from exc
        raise HTTPException(status_code=502, detail="Ошибка сервиса рекомендаций") from exc

    logger.info("[%s] Recommend returned %d items", request_id, len(result.items))
    return RecommendationsOut(
        client_id=client_id,
        items=[
            RecommendationOut(
                product_id=item.product.product_id,
                name=item.product.name,
                insurance_type=item.product.insurance_type,
                basic_tariff=Decimal(item.product.tariff_basis_points).scaleb(-2),
                matching_contracts=item.matching_contracts,
                latest_matching_contract_date=(
                    date.fromisoformat(item.latest_matching_contract_date)
                    if item.HasField("latest_matching_contract_date") else None
                ),
            )
            for item in result.items
        ],
    )
