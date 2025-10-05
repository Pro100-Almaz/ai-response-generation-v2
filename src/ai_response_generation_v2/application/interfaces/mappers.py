from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from ai_response_generation_v2.application.dtos import (
    ArtifactDTO,
    ConversationDTO,
    ConversationWithMessagesDTO,
    CreateConversationDTO,
    CreateMessageDTO,
    MessageDTO,
)
from ai_response_generation_v2.domain.entities import ArtifactEntity, ConversationEntity, MessageEntity


class DtoEntityMapperProtocol(Protocol):
    def to_dto(self, entity: ArtifactEntity) -> ArtifactDTO: ...

    def to_entity(self, dto: ArtifactDTO) -> ArtifactEntity: ...

    def to_dict(self, dto: ArtifactDTO) -> dict: ...

    def from_dict(self, data: dict) -> ArtifactDTO: ...


class ConversationMapperProtocol(Protocol):
    def to_entity(self, dto: CreateConversationDTO, conversation_id: UUID) -> ConversationEntity: ...

    def to_dto(self, entity: ConversationEntity) -> ConversationDTO: ...

    def to_message_entity(self, dto: CreateMessageDTO, message_id: UUID) -> MessageEntity: ...

    def to_message_dto(self, entity: MessageEntity) -> MessageDTO: ...

    def to_conversation_with_messages_dto(
        self, conversation: ConversationEntity, messages: Sequence[MessageEntity]
    ) -> ConversationWithMessagesDTO: ...
