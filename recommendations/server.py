import asyncio
import logging
import os
from collections import Counter
from datetime import date
from uuid import uuid4

import grpc

from recommendations import recommendations_pb2 as messages
from recommendations import recommendations_pb2_grpc as service

logger = logging.getLogger(__name__)


def rank_recommendations(request: messages.RecommendRequest) -> list[messages.Recommendation]:
    limit = request.limit if request.HasField("limit") else 5
    if not 1 <= limit <= 20:
        raise ValueError("limit должен быть от 1 до 20")

    previous_products = set()
    history_counts = Counter()
    latest_dates = {}
    for contract in request.history:
        if contract.product_id <= 0:
            raise ValueError("product_id в истории должен быть положительным")
        previous_products.add(contract.product_id)
        insurance_type = contract.insurance_type.strip().casefold()
        if insurance_type:
            history_counts[insurance_type] += 1
        if contract.HasField("contract_date"):
            try:
                contract_date = date.fromisoformat(contract.contract_date)
                if contract_date.isoformat() != contract.contract_date:
                    raise ValueError
            except ValueError as exc:
                raise ValueError("contract_date должна быть датой YYYY-MM-DD") from exc
            if insurance_type and contract.contract_date > latest_dates.get(insurance_type, ""):
                latest_dates[insurance_type] = contract.contract_date

    candidates = []
    catalog_ids = set()
    for product in request.catalog:
        if product.product_id <= 0 or product.product_id in catalog_ids:
            raise ValueError("product_id в каталоге должен быть положительным и уникальным")
        if not product.HasField("tariff_basis_points") or product.tariff_basis_points < 0:
            raise ValueError("tariff_basis_points должен быть задан и быть неотрицательным")
        catalog_ids.add(product.product_id)
        if product.product_id not in previous_products:
            candidates.append((product, product.insurance_type.strip().casefold()))

    def by_relevance(entry):
        product, insurance_type = entry
        return -history_counts[insurance_type], product.tariff_basis_points, product.product_id

    candidates.sort(key=by_relevance)
    return [
        messages.Recommendation(
            product=product,
            matching_contracts=history_counts[insurance_type],
            latest_matching_contract_date=latest_dates.get(insurance_type),
        )
        for product, insurance_type in candidates[:limit]
    ]


class RecommendationService(service.RecommendationServiceServicer):
    async def _prepare(self, method, request, context):
        request_id = dict(context.invocation_metadata()).get("x-request-id") or uuid4().hex
        logger.info(
            "[%s] %s started: history=%d catalog=%d",
            request_id, method, len(request.history), len(request.catalog),
        )
        try:
            return request_id, rank_recommendations(request)
        except ValueError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))

    async def Recommend(self, request, context):
        request_id, items = await self._prepare("Recommend", request, context)
        logger.info("[%s] Recommend finished: items=%d", request_id, len(items))
        return messages.RecommendResponse(items=items)

    async def StreamRecommendations(self, request, context):
        if not request.HasField("query") or request.delay_ms > 1000:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Требуется query, delay_ms от 0 до 1000")
        request_id, items = await self._prepare("StreamRecommendations", request.query, context)
        for index, item in enumerate(items):
            if index and request.delay_ms:
                await asyncio.sleep(request.delay_ms / 1000)
            logger.info(
                "[%s] StreamRecommendations yielding product_id=%d", request_id, item.product.product_id,
            )
            yield item
        logger.info("[%s] StreamRecommendations finished: items=%d", request_id, len(items))


async def serve():
    address = os.getenv("RECOMMENDATION_GRPC_BIND", "127.0.0.1:50051")
    server = grpc.aio.server()
    service.add_RecommendationServiceServicer_to_server(RecommendationService(), server)
    bound_port = server.add_insecure_port(address)
    await server.start()
    logger.info("RecommendationService listening on %s (port %d, pid %d)", address, bound_port, os.getpid())
    try:
        await server.wait_for_termination()
    finally:
        await server.stop(grace=2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass
