from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal, Sequence, final
from uuid import UUID


MessageRole = Literal["user", "assistant", "system"]
MessageType = Literal["text", "image", "video", "audio", "file", "other"]
AIProvider = Literal["openai", "gemini", "deepseek", "unknown"]
AIInstrument = Literal["chat", "vision", "audio", "other"]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MessageDTO:
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    model: str | None = None
    provider: AIProvider = "unknown"
    instrument: AIInstrument = "chat"
    message_type: MessageType = "text"
    temperature: float | None = None
    max_tokens: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConversationDTO:
    id: UUID
    user_id: int
    title: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConversationWithMessagesDTO:
    conversation: ConversationDTO
    messages: Sequence[MessageDTO]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CreateConversationDTO:
    user_id: int
    title: str | None = None


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CreateMessageDTO:
    conversation_id: UUID
    role: MessageRole
    content: str
    model: str | None = None
    provider: AIProvider = "unknown"
    instrument: AIInstrument = "chat"
    message_type: MessageType = "text"
    temperature: float | None = None
    max_tokens: int | None = None

