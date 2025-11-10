from __future__ import annotations

from dataclasses import dataclass

import structlog

from uuid import UUID

from ai_response_generation_v2.application.dtos import MessageDTO
from ai_response_generation_v2.application.interfaces.ai import (
    AIChatClientFactoryProtocol,
    AIChatClientProtocol,
)
from ai_response_generation_v2.application.interfaces.balance import BalanceControlProtocol


logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerateResponseUseCase:
    ai_client_factory: AIChatClientFactoryProtocol
    balance_control: BalanceControlProtocol
    default_points_cost: int = 20

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
        auth_token: str | None = None,
    ) -> MessageDTO:
        logger.info(
            "Generating response",
            conversation_id=str(conversation_id),
            model=model,
        )

        has_balance = await self.balance_control.check_points(
            auth_token = auth_token,
            minimum_points=self.default_points_cost,
        )
        if not has_balance:
            logger.info("Insufficient balance for response generation")
            raise PermissionError("Insufficient balance")

        messages = [*history, user_message]
        client: AIChatClientProtocol = self.ai_client_factory.get_client(provider, instrument)
        response = await client.generate_response(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=provider,
            instrument=instrument,
        )

        deducted = await self.balance_control.deduct_points(self.default_points_cost)
        if not deducted:
            logger.warning("Failed to deduct points after response generation")
        return response

