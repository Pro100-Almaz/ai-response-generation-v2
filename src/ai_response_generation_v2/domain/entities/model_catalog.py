from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import final
from uuid import UUID


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AIModelEntity:
    id: UUID
    type_id: UUID
    name: str
    display_name: str
    description: str | None = None
    avatar_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AIModelTypeEntity:
    id: UUID
    provider_id: UUID
    identifier: str
    display_name: str
    description: str | None = None
    avatar_url: str | None = None
    models: tuple[AIModelEntity, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AIModelProviderEntity:
    id: UUID
    name: str
    display_name: str
    description: str | None = None
    avatar_url: str | None = None
    types: tuple[AIModelTypeEntity, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

