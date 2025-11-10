from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from ai_response_generation_v2.application.interfaces.repositories import AIModelCatalogRepositoryProtocol
from ai_response_generation_v2.domain.entities.model_catalog import (
    AIModelEntity,
    AIModelProviderEntity,
    AIModelTypeEntity,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListAIModelCatalogUseCase:
    repository: AIModelCatalogRepositoryProtocol

    async def execute(self) -> Sequence[AIModelProviderEntity]:
        return await self.repository.list_catalog()


@dataclass(frozen=True, slots=True, kw_only=True)
class GetOrCreateProviderUseCase:
    repository: AIModelCatalogRepositoryProtocol

    async def execute(
        self,
        *,
        provider_id: UUID,
        name: str,
        display_name: str,
        description: str | None = None,
        avatar_url: str | None = None,
    ) -> AIModelProviderEntity:
        """Get existing provider by name or create a new one with the given ID."""
        existing_provider = await self.repository.get_provider_by_name(name)
        if existing_provider is not None:
            return existing_provider

        # Create new provider with provided ID
        return AIModelProviderEntity(
            id=provider_id,
            name=name,
            display_name=display_name,
            description=description,
            avatar_url=avatar_url,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class GetOrCreateTypeUseCase:
    repository: AIModelCatalogRepositoryProtocol

    async def execute(
        self,
        *,
        type_id: UUID,
        provider_id: UUID,
        identifier: str,
        display_name: str,
        description: str | None = None,
        avatar_url: str | None = None,
    ) -> AIModelTypeEntity:
        """Get existing type by identifier or create a new one with the given ID."""
        existing_type = await self.repository.get_type_by_identifier(identifier)
        if existing_type is not None:
            # Verify it belongs to the same provider
            if existing_type.provider_id != provider_id:
                raise ValueError(
                    f"Type with identifier '{identifier}' already exists but belongs to a different provider"
                )
            return existing_type

        # Create new type with provided ID
        return AIModelTypeEntity(
            id=type_id,
            provider_id=provider_id,
            identifier=identifier,
            display_name=display_name,
            description=description,
            avatar_url=avatar_url,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateAIModelUseCase:
    repository: AIModelCatalogRepositoryProtocol

    async def execute(
        self,
        *,
        provider: AIModelProviderEntity,
        model_type: AIModelTypeEntity,
        model: AIModelEntity,
    ) -> None:
        await self.repository.create_catalog_entries(provider, model_type, model)

