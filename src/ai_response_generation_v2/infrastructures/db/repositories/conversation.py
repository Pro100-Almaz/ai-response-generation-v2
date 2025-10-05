from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ai_response_generation_v2.application.interfaces.repositories import (
    ConversationRepositoryProtocol,
    MessageRepositoryProtocol,
)
from ai_response_generation_v2.domain.entities import ConversationEntity, MessageEntity
from ai_response_generation_v2.domain.exceptions import ConversationNotFoundException
from ai_response_generation_v2.infrastructures.db.exceptions import RepositorySaveError
from ai_response_generation_v2.infrastructures.db.models.conversation import (
    ConversationModel,
    MessageModel,
)


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConversationRepositorySQLAlchemy(ConversationRepositoryProtocol):
    session: AsyncSession

    async def list_by_user(self, user_id: int) -> Sequence[ConversationEntity]:
        stmt = select(ConversationModel).where(ConversationModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return tuple(model.to_entity() for model in result.scalars().all())

    async def get(self, conversation_id: UUID) -> ConversationEntity:
        stmt = select(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ConversationNotFoundException(
                f"Conversation '{conversation_id}' not found"
            )
        return model.to_entity()

    async def create(self, conversation: ConversationEntity) -> ConversationEntity:
        model = ConversationModel.from_entity(conversation)
        self.session.add(model)
        return conversation

    async def update_title(self, conversation_id: UUID, title: str) -> None:
        stmt = select(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ConversationNotFoundException(
                f"Conversation '{conversation_id}' not found"
            )
        model.title = title


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MessageRepositorySQLAlchemy(MessageRepositoryProtocol):
    session: AsyncSession

    async def list_by_conversation(
        self, conversation_id: UUID
    ) -> Sequence[MessageEntity]:
        stmt = select(MessageModel).where(MessageModel.conversation_id == conversation_id)
        result = await self.session.execute(stmt)
        return tuple(message.to_entity() for message in result.scalars().all())

    async def add_message(self, message: MessageEntity) -> None:
        model = MessageModel.from_entity(message)
        self.session.add(model)

    async def bulk_create(self, messages: Sequence[MessageEntity]) -> None:
        try:
            models = [MessageModel.from_entity(message) for message in messages]
            self.session.add_all(models)
        except SQLAlchemyError as exc:
            raise RepositorySaveError(
                f"Failed to persist messages for conversation '{messages[0].conversation_id}'"
            ) from exc

