from __future__ import annotations

from dataclasses import dataclass

import structlog

from ai_response_generation_v2.application.dtos import CreateMessageDTO, MessageDTO
from ai_response_generation_v2.application.interfaces.openai import OpenAIChatClientProtocol


logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerateResponseUseCase:
    openai_client: OpenAIChatClientProtocol

    async def execute(
        self,
        conversation_id: UUID,
        history: list[MessageDTO],
        user_message: MessageDTO,
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> MessageDTO:
        logger.info(
            "Generating response",
            conversation_id=str(conversation_id),
            model=model,
        )

        messages = [*history, user_message]
        return await self.openai_client.generate_response(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

