from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ai_response_generation_v2.application.dtos.conversation import MessageDTO


class AIChatClientProtocol(Protocol):
    async def generate_response(
        self,
        messages: Sequence[MessageDTO],
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        provider: str = "openai",
        instrument: str = "chat",
    ) -> MessageDTO: ...


class AIChatClientFactoryProtocol(Protocol):
    def get_client(self, provider: str, instrument: str) -> AIChatClientProtocol: ...


