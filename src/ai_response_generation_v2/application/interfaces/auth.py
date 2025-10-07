from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from ai_response_generation_v2.application.dtos.conversation import MessageDTO


class AuthorizationServiceProtocol(Protocol):
    async def authorize(self, token: str | None) -> Mapping[str, object]: ...


