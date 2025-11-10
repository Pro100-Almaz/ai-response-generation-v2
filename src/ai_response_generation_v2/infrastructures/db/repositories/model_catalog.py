from __future__ import annotations

from dataclasses import dataclass
from typing import final

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ai_response_generation_v2.application.interfaces.repositories import AIModelCatalogRepositoryProtocol
from ai_response_generation_v2.domain.entities.model_catalog import (
    AIModelEntity,
    AIModelProviderEntity,
    AIModelTypeEntity,
)
from ai_response_generation_v2.infrastructures.db.models.model_catalog import (
    AIModelModel,
    AIModelProviderModel,
    AIModelTypeModel,
)


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AIModelCatalogRepositorySQLAlchemy(AIModelCatalogRepositoryProtocol):
    session: AsyncSession

    async def list_catalog(self) -> tuple[AIModelProviderEntity, ...]:
        provider_stmt = select(AIModelProviderModel).options(
            selectinload(AIModelProviderModel.types)
            .options(selectinload(AIModelTypeModel.models))
        )
        result = await self.session.execute(provider_stmt)
        providers = result.scalars().unique().all()

        provider_entities: list[AIModelProviderEntity] = []
        for provider in providers:
            type_entities = []
            for type_model in sorted(
                provider.types, key=lambda model_type: model_type.display_name
            ):
                models = tuple(
                    model.to_entity()
                    for model in sorted(type_model.models, key=lambda m: m.display_name)
                )
                type_entities.append(type_model.to_entity(models=models))
            provider_entities.append(provider.to_entity(types=tuple(type_entities)))

        return tuple(provider_entities)

    async def get_provider_by_name(self, name: str) -> AIModelProviderEntity | None:
        stmt = select(AIModelProviderModel).where(AIModelProviderModel.name == name)
        result = await self.session.execute(stmt)
        provider_model = result.scalar_one_or_none()
        if provider_model is None:
            return None

        # Load types with models
        await self.session.refresh(provider_model, ["types"])
        type_entities = []
        for type_model in provider_model.types:
            await self.session.refresh(type_model, ["models"])
            models = tuple(model.to_entity() for model in type_model.models)
            type_entities.append(type_model.to_entity(models=models))

        return provider_model.to_entity(types=tuple(type_entities))

    async def get_type_by_identifier(self, identifier: str) -> AIModelTypeEntity | None:
        stmt = select(AIModelTypeModel).where(AIModelTypeModel.identifier == identifier)
        result = await self.session.execute(stmt)
        type_model = result.scalar_one_or_none()
        if type_model is None:
            return None

        # Load models
        await self.session.refresh(type_model, ["models"])
        models = tuple(model.to_entity() for model in type_model.models)

        return type_model.to_entity(models=models)

    async def create_catalog_entries(
        self,
        provider: AIModelProviderEntity,
        model_type: AIModelTypeEntity,
        model: AIModelEntity,
    ) -> None:
        provider_model = await self.session.get(AIModelProviderModel, provider.id)
        if provider_model is None:
            provider_model = AIModelProviderModel(
                id=provider.id,
                name=provider.name,
                display_name=provider.display_name,
                description=provider.description,
                avatar_url=provider.avatar_url,
            )
            self.session.add(provider_model)
        else:
            provider_model.name = provider.name
            provider_model.display_name = provider.display_name
            provider_model.description = provider.description
            provider_model.avatar_url = provider.avatar_url

        type_model = await self.session.get(AIModelTypeModel, model_type.id)
        if type_model is None:
            type_model = AIModelTypeModel(
                id=model_type.id,
                provider_id=provider.id,
                identifier=model_type.identifier,
                display_name=model_type.display_name,
                description=model_type.description,
                avatar_url=model_type.avatar_url,
            )
            self.session.add(type_model)
        else:
            type_model.identifier = model_type.identifier
            type_model.display_name = model_type.display_name
            type_model.description = model_type.description
            type_model.avatar_url = model_type.avatar_url

        model_model = await self.session.get(AIModelModel, model.id)
        if model_model is None:
            model_model = AIModelModel(
                id=model.id,
                type_id=model_type.id,
                name=model.name,
                display_name=model.display_name,
                description=model.description,
                avatar_url=model.avatar_url,
            )
            self.session.add(model_model)
        else:
            model_model.name = model.name
            model_model.display_name = model.display_name
            model_model.description = model.description
            model_model.avatar_url = model.avatar_url

