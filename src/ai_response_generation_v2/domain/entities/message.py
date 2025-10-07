from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal, final
from uuid import UUID


Role = Literal["user", "assistant", "system"]
AIProvider = Literal["openai", "gemini", "deepseek", "unknown"]
AIInstrument = Literal["chat", "vision", "audio", "other"]
MessageType = Literal["text", "image", "video", "audio", "file", "other"]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MessageEntity:
    id: UUID
    conversation_id: UUID
    role: Role
    content: str
    model: str | None = None
    provider: AIProvider = "unknown"
    instrument: AIInstrument = "chat"
    message_type: MessageType = "text"
    temperature: float | None = None
    max_tokens: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


