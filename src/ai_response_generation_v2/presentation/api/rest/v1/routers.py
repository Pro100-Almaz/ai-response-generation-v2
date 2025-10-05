from fastapi import APIRouter

from ai_response_generation_v2.presentation.api.rest.v1.controllers.artifact_controller import (
    router as artifact_router,
)
from ai_response_generation_v2.presentation.api.rest.v1.controllers.chat_controller import (
    router as chat_router,
)

api_v1_router = APIRouter()
api_v1_router.include_router(artifact_router)
api_v1_router.include_router(chat_router)
