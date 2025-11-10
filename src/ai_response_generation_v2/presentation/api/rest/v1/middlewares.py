from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from dishka import AsyncContainer

from ai_response_generation_v2.application.interfaces.auth import AuthorizationServiceProtocol


RequestHandler = Callable[[Request], Awaitable[Response]]


class AuthorizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, container, exempt_paths: set[str] | None = None) -> None:
        super().__init__(app)
        self._root_container = container
        self._exempt_paths = set(exempt_paths or ())
        self._exempt_paths.update(("/api/docs", "/api/redoc", "/api/openapi.json"))

    async def dispatch(self, request: Request, call_next: RequestHandler) -> Response:
        if request.url.path in self._exempt_paths:
            return await call_next(request)

        req_container: AsyncContainer | None = getattr(request.state, "dishka_container", None)
        container = req_container or self._root_container  # fallback just in case

        # Extract bearer token
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.split(" ", 1)[1] if auth_header.lower().startswith("bearer ") else None

        try:
            authorizer = await container.get(AuthorizationServiceProtocol)
            claims = await authorizer.authorize(token)
        except PermissionError:
            raise

        # Stash user context for downstream handlers
        request.state.user = {
            "id": claims.get("user_id") or claims.get("sub"),
            **claims,
        }

        request.state.auth_token = auth_header

        return await call_next(request)

