from __future__ import annotations

from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ai_response_generation_v2.application.interfaces.auth import AuthorizationServiceProtocol


class AuthorizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, authorizer: AuthorizationServiceProtocol, exempt_paths: set[str] | None = None) -> None:
        super().__init__(app)
        self._authorizer = authorizer
        self._exempt_paths = exempt_paths or set()

    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path in self._exempt_paths:
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        token = None
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]

        claims = await self._authorizer.authorize(token)
        request.state.user = claims
        return await call_next(request)

