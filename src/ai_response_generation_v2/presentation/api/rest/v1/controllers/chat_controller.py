from __future__ import annotations

import dataclasses
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, Request, status

from ai_response_generation_v2.application.dtos import (
    CreateConversationDTO,
    CreateMessageDTO,
    MessageRole,
)
from ai_response_generation_v2.application.use_cases import (
    AddMessageUseCase,
    CreateConversationUseCase,
    GenerateResponseUseCase,
    GetConversationHistoryUseCase,
    ListConversationsUseCase,
)
from ai_response_generation_v2.presentation.api.rest.v1.schemas.chat import (
    ChatModelListResponse,
    ConversationCreateRequest,
    ConversationResponse,
    ConversationWithMessagesResponse,
    MessageCreateRequest,
    MessageResponse,
    MessageWithReplyResponse,
)
from ai_response_generation_v2.presentation.services.ai_catalog import AICatalogService


router = APIRouter(prefix="/v1/chat", tags=["Chat"])


def _to_message_role(role: str) -> MessageRole:
    if role not in ("user", "assistant", "system"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    return role  # type: ignore[return-value]


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_conversation(
    payload: ConversationCreateRequest,
    use_case: FromDishka[CreateConversationUseCase],
) -> ConversationResponse:
    dto = CreateConversationDTO(user_id=payload.user_id, title=payload.title)
    result = await use_case.execute(dto)
    return ConversationResponse.model_validate(dataclasses.asdict(result))


@router.get("/conversations", response_model=list[ConversationResponse])
@inject
async def list_conversations(
    request: Request,
    use_case: FromDishka[ListConversationsUseCase],
) -> list[ConversationResponse]:
    claims = getattr(request.state, "user", None) or {}
    user_id = claims.get("user_id") or claims.get("sub")

    conversations = await use_case.execute(user_id)
    return [ConversationResponse.model_validate(dataclasses.asdict(conversation)) for conversation in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessagesResponse)
@inject
async def get_conversation_history(
    conversation_id: UUID,
    use_case: FromDishka[GetConversationHistoryUseCase],
) -> ConversationWithMessagesResponse:
    result = await use_case.execute(conversation_id)
    return ConversationWithMessagesResponse(
        conversation=ConversationResponse.model_validate(dataclasses.asdict(result.conversation)),
        messages=[MessageResponse.model_validate(dataclasses.asdict(message)) for message in result.messages],
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageWithReplyResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_message_with_completion(
    conversation_id: UUID,
    payload: MessageCreateRequest,
    add_message_use_case: FromDishka[AddMessageUseCase],
    history_use_case: FromDishka[GetConversationHistoryUseCase],
    generate_use_case: FromDishka[GenerateResponseUseCase],
) -> MessageWithReplyResponse:
    history = await history_use_case.execute(conversation_id)
    user_message_dto = CreateMessageDTO(
        conversation_id=conversation_id,
        role=_to_message_role(payload.role),
        content=payload.content,
        model=payload.model,
        provider=payload.provider,
        instrument=payload.instrument,
        message_type=payload.message_type,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )

    stored_user_message = await add_message_use_case.execute(user_message_dto)

    assistant_message = await generate_use_case.execute(
        conversation_id=conversation_id,
        history=list(history.messages),
        user_message=stored_user_message,
        model=payload.model or stored_user_message.model or "",
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        provider=payload.provider,
        instrument=payload.instrument,
    )

    stored_assistant_message = await add_message_use_case.execute(
        CreateMessageDTO(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_message.content,
            model=assistant_message.model,
            provider=assistant_message.provider,
            instrument=assistant_message.instrument,
            message_type=assistant_message.message_type,
            temperature=assistant_message.temperature,
            max_tokens=assistant_message.max_tokens,
        )
    )

    return MessageWithReplyResponse(
        user_message=MessageResponse.model_validate(dataclasses.asdict(stored_user_message)),
        assistant_message=MessageResponse.model_validate(dataclasses.asdict(stored_assistant_message)),
    )


@router.get("/models", response_model=ChatModelListResponse)
async def list_models() -> ChatModelListResponse:
    return ChatModelListResponse.model_validate(AICatalogService().list_models())

