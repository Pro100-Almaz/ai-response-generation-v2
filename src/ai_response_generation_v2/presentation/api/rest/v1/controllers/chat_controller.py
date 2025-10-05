from __future__ import annotations

from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, status

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
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatModelListResponse,
    ConversationCreateRequest,
    ConversationResponse,
    ConversationWithMessagesResponse,
    MessageCreateRequest,
    MessageResponse,
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
    return ConversationResponse.model_validate(result)


@router.get("/conversations", response_model=list[ConversationResponse])
@inject
async def list_conversations(
    user_id: int,
    use_case: FromDishka[ListConversationsUseCase],
) -> list[ConversationResponse]:
    conversations = await use_case.execute(user_id)
    return [ConversationResponse.model_validate(conversation) for conversation in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessagesResponse)
@inject
async def get_conversation_history(
    conversation_id: UUID,
    use_case: FromDishka[GetConversationHistoryUseCase],
) -> ConversationWithMessagesResponse:
    result = await use_case.execute(conversation_id)
    return ConversationWithMessagesResponse(
        conversation=ConversationResponse.model_validate(result.conversation),
        messages=[MessageResponse.model_validate(message) for message in result.messages],
    )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@inject
async def add_message(
    conversation_id: UUID,
    payload: MessageCreateRequest,
    use_case: FromDishka[AddMessageUseCase],
) -> MessageResponse:
    dto = CreateMessageDTO(
        conversation_id=conversation_id,
        role=_to_message_role(payload.role),
        content=payload.content,
        model=payload.model,
        ai_type=payload.ai_type or "unknown",
        message_type=payload.message_type,
    )
    result = await use_case.execute(dto)
    return MessageResponse.model_validate(result)


@router.post("/conversations/{conversation_id}/messages:generate", response_model=ChatCompletionResponse)
@inject
async def generate_completion(
    conversation_id: UUID,
    payload: ChatCompletionRequest,
    add_message_use_case: FromDishka[AddMessageUseCase],
    history_use_case: FromDishka[GetConversationHistoryUseCase],
    generate_use_case: FromDishka[GenerateResponseUseCase],
) -> ChatCompletionResponse:
    history = await history_use_case.execute(conversation_id)
    user_message_dto = CreateMessageDTO(
        conversation_id=conversation_id,
        role=_to_message_role(payload.message.role),
        content=payload.message.content,
        model=payload.message.model,
        ai_type=payload.message.ai_type or payload.provider,
        message_type=payload.message.message_type,
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
            ai_type=assistant_message.ai_type,
            message_type=assistant_message.message_type,
        )
    )

    return ChatCompletionResponse(
        conversation=ConversationResponse.model_validate(history.conversation),
        user_message=MessageResponse.model_validate(stored_user_message),
        assistant_message=MessageResponse.model_validate(stored_assistant_message),
    )


@router.get("/models", response_model=ChatModelListResponse)
async def list_models() -> ChatModelListResponse:
    return ChatModelListResponse.model_validate(AICatalogService().list_models())

