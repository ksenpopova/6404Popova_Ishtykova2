import os
from contextlib import asynccontextmanager

import grpc
from fastapi import FastAPI, Request

from recommendations.recommendations_pb2_grpc import RecommendationServiceStub


@asynccontextmanager
async def recommendation_lifespan(app: FastAPI):
    target = os.getenv("RECOMMENDATION_GRPC_TARGET", "127.0.0.1:50051")
    with grpc.insecure_channel(target) as channel:
        app.state.recommendation_client = RecommendationServiceStub(channel)
        yield


def get_recommendation_client(request: Request) -> RecommendationServiceStub:
    return request.app.state.recommendation_client
