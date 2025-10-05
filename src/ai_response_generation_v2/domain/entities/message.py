from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal, final
from uuid import UUID


Role = Literal["user", "assistant", "system"]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MessageEntity:
    id: UUID
    conversation_id: UUID
    role: Role
    content: str
    model: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


