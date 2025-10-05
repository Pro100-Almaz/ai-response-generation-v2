from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


MessageRoleLiteral = Literal["user", "assistant", "system"]


class ConversationCreateRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    title: str | None = Field(None, max_length=255)


class MessageCreateRequest(BaseModel):
    role: MessageRoleLiteral
    content: str = Field(..., min_length=1)
    model: str | None = None


class ChatCompletionRequest(BaseModel):
    message: MessageCreateRequest
    model: str | None = None
    temperature: float | None = Field(None, ge=0, le=2)
    max_tokens: int | None = Field(None, ge=1)


class ConversationResponse(BaseModel):
    id: UUID
    user_id: int
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRoleLiteral
    content: str
    model: str | None
    created_at: datetime


class ConversationWithMessagesResponse(BaseModel):
    conversation: ConversationResponse
    messages: list[MessageResponse]


class ChatCompletionResponse(BaseModel):
    conversation: ConversationResponse
    user_message: MessageResponse
    assistant_message: MessageResponse

