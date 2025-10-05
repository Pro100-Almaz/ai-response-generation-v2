from __future__ import annotations

from dataclasses import dataclass

import structlog

from uuid import UUID

from ai_response_generation_v2.application.dtos import MessageDTO
from ai_response_generation_v2.application.interfaces.ai import (
    AIChatClientFactoryProtocol,
    AIChatClientProtocol,
)


logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerateResponseUseCase:
    ai_client_factory: AIChatClientFactoryProtocol

    async def execute(
        self,
        conversation_id: UUID,
        history: list[MessageDTO],
        user_message: MessageDTO,
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        provider: str = "openai",
        instrument: str = "chat",
    ) -> MessageDTO:
        logger.info(
            "Generating response",
            conversation_id=str(conversation_id),
            model=model,
        )

        messages = [*history, user_message]
        client: AIChatClientProtocol = self.ai_client_factory.get_client(provider, instrument)
        return await client.generate_response(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=provider,
            instrument=instrument,
        )

