from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence
from uuid import UUID, uuid4

import structlog

from ai_response_generation_v2.application.dtos import (
    ConversationDTO,
    ConversationWithMessagesDTO,
    CreateConversationDTO,
    CreateMessageDTO,
    MessageDTO,
)
from ai_response_generation_v2.application.interfaces.mappers import ConversationMapperProtocol
from ai_response_generation_v2.application.interfaces.repositories import (
    ConversationRepositoryProtocol,
    MessageRepositoryProtocol,
)
from ai_response_generation_v2.application.interfaces.uow import UnitOfWorkProtocol


logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateConversationUseCase:
    uow: UnitOfWorkProtocol
    mapper: ConversationMapperProtocol

    async def execute(self, dto: CreateConversationDTO) -> ConversationDTO:
        logger.info("Creating conversation", user_id=dto.user_id, title=dto.title)
        conversation_entity = self.mapper.to_entity(dto, uuid4())

        async with self.uow:
            await self.uow.conversations.create(conversation_entity)

        return self.mapper.to_dto(conversation_entity)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetConversationHistoryUseCase:
    conversations: ConversationRepositoryProtocol
    messages: MessageRepositoryProtocol
    mapper: ConversationMapperProtocol

    async def execute(self, conversation_id: UUID) -> ConversationWithMessagesDTO:
        logger.debug("Fetching conversation history", conversation_id=str(conversation_id))
        conversation = await self.conversations.get(conversation_id)
        history: Sequence = await self.messages.list_by_conversation(conversation_id)
        return self.mapper.to_conversation_with_messages_dto(conversation, history)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListConversationsUseCase:
    conversations: ConversationRepositoryProtocol
    mapper: ConversationMapperProtocol

    async def execute(self, user_id: int) -> Sequence[ConversationDTO]:
        logger.debug("Listing conversations", user_id=user_id)
        convs = await self.conversations.list_by_user(user_id)
        return tuple(self.mapper.to_dto(conversation) for conversation in convs)


@dataclass(frozen=True, slots=True, kw_only=True)
class AddMessageUseCase:
    uow: UnitOfWorkProtocol
    mapper: ConversationMapperProtocol

    async def execute(self, dto: CreateMessageDTO) -> MessageDTO:
        message_entity = self.mapper.to_message_entity(dto, uuid4())

        async with self.uow:
            await self.uow.messages.add_message(message_entity)

        return self.mapper.to_message_dto(message_entity)

