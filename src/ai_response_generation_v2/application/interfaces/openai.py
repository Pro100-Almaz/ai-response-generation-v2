from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ai_response_generation_v2.application.dtos.conversation import MessageDTO


class OpenAIChatClientProtocol(Protocol):
    async def generate_response(
        self,
        messages: Sequence[MessageDTO],
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> MessageDTO: ...

