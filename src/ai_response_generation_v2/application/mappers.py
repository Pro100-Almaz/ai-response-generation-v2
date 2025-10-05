from dataclasses import dataclass
from datetime import datetime
from typing import Sequence, final
from uuid import UUID

from ai_response_generation_v2.application.dtos import (
    ArtifactDTO,
    ConversationDTO,
    ConversationWithMessagesDTO,
    CreateConversationDTO,
    CreateMessageDTO,
    EraDTO,
    MaterialDTO,
    MessageDTO,
)
from ai_response_generation_v2.application.interfaces.mappers import (
    ConversationMapperProtocol,
    DtoEntityMapperProtocol,
)
from ai_response_generation_v2.domain.entities import (
    ArtifactEntity,
    ConversationEntity,
    MessageEntity,
)
from ai_response_generation_v2.domain.value_objects.era import Era
from ai_response_generation_v2.domain.value_objects.material import Material


@final
@dataclass(frozen=True, slots=True)
class ArtifactMapper(DtoEntityMapperProtocol):
    def to_dto(self, entity: ArtifactEntity) -> ArtifactDTO:
        return ArtifactDTO(
            inventory_id=entity.inventory_id,
            created_at=entity.created_at,
            acquisition_date=entity.acquisition_date,
            name=entity.name,
            department=entity.department,
            era=EraDTO(value=entity.era.value),
            material=MaterialDTO(value=entity.material.value),
            description=entity.description,
        )

    def to_entity(self, dto: ArtifactDTO) -> ArtifactEntity:
        return ArtifactEntity(
            inventory_id=dto.inventory_id,
            name=dto.name,
            acquisition_date=dto.acquisition_date,
            department=dto.department,
            era=Era(value=dto.era.value),
            material=Material(value=dto.material.value),
            description=dto.description,
        )

    def to_dict(self, dto: ArtifactDTO) -> dict:
        return {
            "inventory_id": str(dto.inventory_id),
            "created_at": dto.created_at.isoformat(),
            "acquisition_date": dto.acquisition_date.isoformat(),
            "name": dto.name,
            "department": dto.department,
            "era": {"value": dto.era.value},
            "material": {"value": dto.material.value},
            "description": dto.description,
        }

    def from_dict(self, data: dict) -> ArtifactDTO:
        return ArtifactDTO(
            inventory_id=UUID(data["inventory_id"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            acquisition_date=datetime.fromisoformat(data["acquisition_date"]),
            name=data["name"],
            department=data["department"],
            era=EraDTO(value=data["era"]["value"]),
            material=MaterialDTO(value=data["material"]["value"]),
            description=data.get("description"),
        )


@final
@dataclass(frozen=True, slots=True)
class ConversationMapper(ConversationMapperProtocol):
    def to_entity(self, dto: CreateConversationDTO, conversation_id: UUID) -> ConversationEntity:
        return ConversationEntity(id=conversation_id, user_id=dto.user_id, title=dto.title)

    def to_dto(self, entity: ConversationEntity) -> ConversationDTO:
        return ConversationDTO(
            id=entity.id,
            user_id=entity.user_id,
            title=entity.title,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_message_entity(self, dto: CreateMessageDTO, message_id: UUID) -> MessageEntity:
        return MessageEntity(
            id=message_id,
            conversation_id=dto.conversation_id,
            role=dto.role,
            content=dto.content,
            model=dto.model,
            ai_type=dto.ai_type,
            message_type=dto.message_type,
        )

    def to_message_dto(self, entity: MessageEntity) -> MessageDTO:
        return MessageDTO(
            id=entity.id,
            conversation_id=entity.conversation_id,
            role=entity.role,
            content=entity.content,
            model=entity.model,
            ai_type=entity.ai_type,
            message_type=entity.message_type,
            created_at=entity.created_at,
        )

    def to_conversation_with_messages_dto(
        self, conversation: ConversationEntity, messages: Sequence[MessageEntity]
    ) -> ConversationWithMessagesDTO:
        return ConversationWithMessagesDTO(
            conversation=self.to_dto(conversation),
            messages=tuple(self.to_message_dto(message) for message in messages),
        )
