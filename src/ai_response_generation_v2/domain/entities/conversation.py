from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import final
from uuid import UUID


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConversationEntity:
    id: UUID
    user_id: int
    title: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


