from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import final
from uuid import UUID

from ai_response_generation_v2.domain.value_objects.era import Era
from ai_response_generation_v2.domain.value_objects.material import Material


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactEntity:
    inventory_id: UUID
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    acquisition_date: datetime
    name: str
    department: str
    era: Era
    material: Material
    description: str | None = None
