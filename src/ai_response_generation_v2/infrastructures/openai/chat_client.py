from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, final
from uuid import uuid4

from openai import AsyncOpenAI

from ai_response_generation_v2.application.dtos.conversation import MessageDTO
from ai_response_generation_v2.application.interfaces.ai import AIChatClientProtocol


def _extract_content(raw: str | Sequence[dict[str, str]] | None) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, Sequence):
        return "".join(part.get("text", "") for part in raw if isinstance(part, dict))
    return ""


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OpenAIChatClient(AIChatClientProtocol):
    client: AsyncOpenAI
    default_model: str | None = None
    default_temperature: float | None = None
    default_max_tokens: int | None = None

    async def generate_response(
        self,
        messages: Sequence[MessageDTO],
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        provider: str = "openai",
        instrument: str = "chat",
    ) -> MessageDTO:
        if provider != "openai":
            raise ValueError(f"Unsupported provider '{provider}' for OpenAIChatClient")
        if instrument != "chat":
            raise ValueError(f"Unsupported instrument '{instrument}' for OpenAIChatClient")
        if not messages:
            raise ValueError("Messages history cannot be empty when generating a response")

        model_name = model or self.default_model or "gpt-4o-mini"
        temperature_value = temperature if temperature is not None else self.default_temperature
        max_tokens_value = max_tokens if max_tokens is not None else self.default_max_tokens

        payload = [
            {"role": message.role, "content": message.content}
            for message in messages
        ]

        response = await self.client.chat.completions.create(
            model=model_name,
            messages=payload,
            temperature=temperature_value,
            max_tokens=max_tokens_value,
        )

        choice = response.choices[0]
        content = _extract_content(choice.message.content)
        used_model = getattr(response, "model", None) or model_name

        conversation_id = messages[-1].conversation_id

        return MessageDTO(
            id=uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            model=used_model,
            provider="openai",
            instrument="chat",
            message_type="text",
            temperature=temperature_value,
            max_tokens=max_tokens_value,
        )

