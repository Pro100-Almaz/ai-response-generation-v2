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
    CreateAIModelUseCase,
    CreateConversationUseCase,
    GenerateResponseUseCase,
    GetConversationHistoryUseCase,
    GetOrCreateProviderUseCase,
    GetOrCreateTypeUseCase,
    ListConversationsUseCase,
)
from ai_response_generation_v2.presentation.api.rest.v1.schemas.chat import (
    ChatModelCreateRequest,
    ChatModelListResponse,
    ConversationCreateRequest,
    ConversationResponse,
    ConversationWithMessagesResponse,
    MessageCreateRequest,
    MessageResponse,
    MessageWithReplyResponse,
)
from ai_response_generation_v2.presentation.services.ai_catalog import AICatalogService
from ai_response_generation_v2.domain.entities.model_catalog import (
    AIModelEntity,
    AIModelProviderEntity,
    AIModelTypeEntity,
)
from ai_response_generation_v2.application.interfaces.auth import AuthorizationServiceProtocol


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
    request: Request,
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

    auth_token = getattr(request.state, "auth_token", None) or {}

    try:
        assistant_message = await generate_use_case.execute(
            conversation_id=conversation_id,
            history=list(history.messages),
            user_message=stored_user_message,
            model=payload.model or stored_user_message.model or "",
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            provider=payload.provider,
            instrument=payload.instrument,
            auth_token=auth_token
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(exc) or "Insufficient balance",
        ) from exc

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
@inject
async def list_models(
    catalog_service: FromDishka[AICatalogService],
) -> ChatModelListResponse:
    catalog_payload = await catalog_service.list_models()
    return ChatModelListResponse.model_validate(catalog_payload)


@router.post(
    "/models",
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_models(
    request: Request,
    payload: ChatModelCreateRequest,
    get_or_create_provider_use_case: FromDishka[GetOrCreateProviderUseCase],
    get_or_create_type_use_case: FromDishka[GetOrCreateTypeUseCase],
    create_use_case: FromDishka[CreateAIModelUseCase],
) -> None:
    claims = getattr(request.state, "user", {})
    roles = claims.get("roles")
    if roles is None:
        roles = []
    elif isinstance(roles, str):
        roles = [roles]

    if "tool_creator" not in set(roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    provider_payload = payload.provider
    if not provider_payload.types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider types are required",
        )

    # Get or create provider (will use existing ID if found by name, or create with provided ID)
    provider_entity = await get_or_create_provider_use_case.execute(
        provider_id=provider_payload.id,
        name=provider_payload.name,
        display_name=provider_payload.display_name,
        description=provider_payload.description,
        avatar_url=provider_payload.avatar_url,
    )

    for type_payload in provider_payload.types:
        if not type_payload.models:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type '{type_payload.identifier}' must include at least one model",
            )

        # Get or create type (will use existing ID if found by identifier, or create with provided ID)
        try:
            type_entity = await get_or_create_type_use_case.execute(
                type_id=type_payload.id,
                provider_id=provider_entity.id,  # Use the actual provider ID (may differ from payload)
                identifier=type_payload.identifier,
                display_name=type_payload.display_name,
                description=type_payload.description,
                avatar_url=type_payload.avatar_url,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        for model_payload in type_payload.models:
            model_entity = AIModelEntity(
                id=model_payload.id,
                type_id=type_entity.id,  # Use the actual type ID (may differ from payload)
                name=model_payload.name,
                display_name=model_payload.display_name,
                description=model_payload.description,
                avatar_url=model_payload.avatar_url,
            )
            await create_use_case.execute(
                provider=provider_entity,
                model_type=type_entity,
                model=model_entity,
            )

