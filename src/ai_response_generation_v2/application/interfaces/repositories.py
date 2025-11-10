from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from ai_response_generation_v2.domain.entities import (
    ArtifactEntity,
    ConversationEntity,
    MessageEntity,
    AIModelEntity,
    AIModelProviderEntity,
    AIModelTypeEntity,
)


class ArtifactRepositoryProtocol(Protocol):
    async def get_by_inventory_id(
        self, inventory_id: str | UUID
    ) -> ArtifactEntity | None: ...

    async def save(self, artifact: ArtifactEntity) -> None: ...


class ConversationRepositoryProtocol(Protocol):
    async def list_by_user(self, user_id: int) -> Sequence[ConversationEntity]: ...

    async def get(self, conversation_id: UUID) -> ConversationEntity: ...

    async def create(self, conversation: ConversationEntity) -> ConversationEntity: ...

    async def update_title(self, conversation_id: UUID, title: str) -> None: ...


class MessageRepositoryProtocol(Protocol):
    async def list_by_conversation(
        self, conversation_id: UUID
    ) -> Sequence[MessageEntity]: ...

    async def add_message(self, message: MessageEntity) -> None: ...

    async def bulk_create(self, messages: Sequence[MessageEntity]) -> None: ...


class AIModelCatalogRepositoryProtocol(Protocol):
    async def list_catalog(self) -> Sequence[AIModelProviderEntity]: ...

    async def get_provider_by_name(self, name: str) -> AIModelProviderEntity | None: ...

    async def get_type_by_identifier(self, identifier: str) -> AIModelTypeEntity | None: ...

    async def create_catalog_entries(
        self,
        provider: AIModelProviderEntity,
        model_type: AIModelTypeEntity,
        model: AIModelEntity,
    ) -> None: ...
