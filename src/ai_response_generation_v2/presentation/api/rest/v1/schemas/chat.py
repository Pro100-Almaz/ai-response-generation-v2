from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


MessageRoleLiteral = Literal["user", "assistant", "system"]
AIProviderLiteral = Literal["openai"]
AIInstrumentLiteral = Literal["chat"]
MessageTypeLiteral = Literal["text", "image", "video", "audio", "file", "other"]


class ConversationCreateRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    title: str | None = Field(None, max_length=255)


class MessageCreateRequest(BaseModel):
    role: MessageRoleLiteral
    content: str = Field(..., min_length=1)
    model: str | None = None
    provider: AIProviderLiteral = Field("openai")
    instrument: AIInstrumentLiteral = Field("chat")
    message_type: MessageTypeLiteral = "text"
    temperature: float | None = Field(None, ge=0, le=0.7)
    max_tokens: int | None = Field(None, ge=320)


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
    provider: AIProviderLiteral
    instrument: AIInstrumentLiteral
    message_type: MessageTypeLiteral
    temperature: float | None
    max_tokens: int | None
    created_at: datetime


class MessageWithReplyResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class ConversationWithMessagesResponse(BaseModel):
    conversation: ConversationResponse
    messages: list[MessageResponse]


class ChatCompletionResponse(BaseModel):
    conversation: ConversationResponse
    user_message: MessageResponse
    assistant_message: MessageResponse


class ChatModelResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: str | None = None
    avatar_url: str | None = None


class ChatModelTypeResponse(BaseModel):
    id: UUID
    identifier: str
    display_name: str
    description: str | None = None
    avatar_url: str | None = None
    models: list[ChatModelResponse]


class ChatModelProviderResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: str | None = None
    avatar_url: str | None = None
    types: list[ChatModelTypeResponse]


class ChatModelListResponse(BaseModel):
    providers: list[ChatModelProviderResponse]


class ChatModelCreateModelPayload(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: str | None = None
    avatar_url: str | None = None


class ChatModelCreateTypePayload(BaseModel):
    id: UUID
    identifier: str
    display_name: str
    description: str | None = None
    avatar_url: str | None = None
    models: list[ChatModelCreateModelPayload]


class ChatModelCreateProviderPayload(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: str | None = None
    avatar_url: str | None = None
    types: list[ChatModelCreateTypePayload]


class ChatModelCreateRequest(BaseModel):
    provider: ChatModelCreateProviderPayload

