from __future__ import annotations

import json
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any

import httpx
from jwt import JWT, jwk_from_pem
import structlog

from ai_response_generation_v2.application.interfaces.auth import AuthorizationServiceProtocol


logger = structlog.get_logger(__name__)


@dataclass(slots=True, frozen=True, kw_only=True)
class MonolithAuthorizationService(AuthorizationServiceProtocol):
    base_url: str
    audience: str
    timeout: float
    client: httpx.AsyncClient
    public_key: bytes

    async def authorize(self, token: str | None) -> Mapping[str, object]:
        if not token:
            raise PermissionError("Missing bearer token")

        claims = self._decode_token(token)
        user_id = claims.get("sub") or claims.get("user_id")
        if not user_id:
            raise PermissionError("Token missing subject")

        if self.base_url:
            url = f"{self.base_url.rstrip('/')}/api/token/verify/"
            payload = {"token": token, "audience": self.audience}
            logger.debug("Authorizing user via monolith", url=url, user_id=user_id)

            # try:
            #     response = await self.client.post(url, json=payload, timeout=self.timeout)
            #     response.raise_for_status()
            # except httpx.HTTPStatusError as exc:  # pragma: no cover - just defensive logging
            #     logger.warning(
            #         "Authorization failed", status_code=exc.response.status_code, detail=exc.response.text
            #     )
            #
            #     raise PermissionError("Authorization rejected by monolith") from exc
            # except httpx.RequestError as exc:
            #     logger.error("Authorization request error", error=str(exc))
            #     raise PermissionError("Unable to contact authorization service") from exc

        return {"user_id": user_id, **claims}

    def _decode_token(self, token: str) -> Mapping[str, Any]:
        instance = JWT()
        verifying_key = jwk_from_pem(self.public_key)
        try:
            return instance.decode(
                token,
                verifying_key,
                do_time_check=True,
                algorithms={"RS256"},
            )
        except Exception as exc:
            logger.warning("Token verification failed", error=str(exc))
            raise PermissionError("Invalid bearer token") from exc

