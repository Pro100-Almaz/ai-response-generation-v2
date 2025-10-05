from dataclasses import dataclass, field
import json
from typing import final

import structlog
from faststream.kafka import KafkaBroker

from ai_response_generation_v2.application.dtos.artifact import ArtifactAdmissionNotificationDTO
from ai_response_generation_v2.application.interfaces.message_broker import MessageBrokerPublisherProtocol
from ai_response_generation_v2.infrastructures.dtos.artifact import (
    ArtifactAdmissionNotificationPydanticDTO,
)
from ai_response_generation_v2.infrastructures.mappers.artifact import InfrastructureArtifactMapper


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class KafkaPublisher(MessageBrokerPublisherProtocol):
    broker: KafkaBroker
    topic: str = field(default="new_artifacts")
    mapper: InfrastructureArtifactMapper

    async def publish_new_artifact(
        self, artifact: ArtifactAdmissionNotificationDTO
    ) -> None:
        try:
            pydantic_artifact = self.mapper.to_admission_notification_pydantic(artifact)
            await self.broker.publish(
                key=pydantic_artifact.inventory_id,
                message=json.dumps(pydantic_artifact.model_dump(), ensure_ascii=False),
                topic=self.topic,
            )
        except Exception as e:
            logger = structlog.get_logger(__name__)
            logger.error("Failed to publish artifact", error=str(e))
            raise
