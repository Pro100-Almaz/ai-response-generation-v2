from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_response_generation_v2.config.ioc.di import get_providers
from ai_response_generation_v2.config.logging import setup_logging
from ai_response_generation_v2.presentation.api.rest.v1.routers import api_v1_router
from ai_response_generation_v2.presentation.api.rest.v1.middlewares import AuthorizationMiddleware
from ai_response_generation_v2.config.exceptions import install_exception_middleware

setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting application...")
    yield
    logger.info("Shutting down application...")


def create_app() -> FastAPI:
    container: AsyncContainer = make_async_container(*get_providers())

    app = FastAPI(
        title="ai-response-generation-v2 API",
        version="1.0.0",
        description="API for A modern FastAPI project to use multi AI models in one service",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        AuthorizationMiddleware, # type: ignore
        container=container,
        exempt_paths={
            "/api/v1/health",
            "/api/v1/chat/models",
        },
    )

    app.add_middleware(  # type: ignore[call-arg]
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=["http://localhost:3000", "https://project-x.space", "https://www.project-x.space"],
        allow_credentials=True,
        allow_methods=["GET","POST","PUT","DELETE","OPTIONS"],
        allow_headers=["*"],
    )

    setup_dishka(container, app)

    install_exception_middleware(app)

    app.include_router(api_v1_router, prefix="/api")

    return app


app = create_app()
