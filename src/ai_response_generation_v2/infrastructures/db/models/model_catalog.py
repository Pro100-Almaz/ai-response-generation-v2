from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai_response_generation_v2.domain.entities.model_catalog import (
    AIModelEntity,
    AIModelProviderEntity,
    AIModelTypeEntity,
)
from ai_response_generation_v2.infrastructures.db.models.artifact import mapper_registry


@mapper_registry.mapped
class AIModelProviderModel:
    __tablename__ = "ai_model_providers"

    __table_args__ = (
        Index("ix_ai_model_providers_name", "name", unique=True),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(length=64), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(length=128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=func.now(),
    )

    types: Mapped[list["AIModelTypeModel"]] = relationship(
        back_populates="provider",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_entity(self, types: tuple[AIModelTypeEntity, ...]) -> AIModelProviderEntity:
        return AIModelProviderEntity(
            id=self.id,
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            avatar_url=self.avatar_url,
            types=types,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


@mapper_registry.mapped
class AIModelTypeModel:
    __tablename__ = "ai_model_types"

    __table_args__ = (
        Index("ix_ai_model_types_identifier", "identifier", unique=True),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ai_model_providers.id", ondelete="CASCADE"),
        nullable=False,
    )
    identifier: Mapped[str] = mapped_column(String(length=64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(length=128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=func.now(),
    )

    provider: Mapped[AIModelProviderModel] = relationship(
        back_populates="types",
    )
    models: Mapped[list["AIModelModel"]] = relationship(
        back_populates="type",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_entity(self, models: tuple[AIModelEntity, ...]) -> AIModelTypeEntity:
        return AIModelTypeEntity(
            id=self.id,
            provider_id=self.provider_id,
            identifier=self.identifier,
            display_name=self.display_name,
            description=self.description,
            avatar_url=self.avatar_url,
            models=models,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


@mapper_registry.mapped
class AIModelModel:
    __tablename__ = "ai_models"

    __table_args__ = (
        Index("ix_ai_models_name", "name", unique=True),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )
    type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ai_model_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(length=128), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(length=128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=func.now(),
    )

    type: Mapped[AIModelTypeModel] = relationship(
        back_populates="models",
    )

    def to_entity(self) -> AIModelEntity:
        return AIModelEntity(
            id=self.id,
            type_id=self.type_id,
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            avatar_url=self.avatar_url,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

