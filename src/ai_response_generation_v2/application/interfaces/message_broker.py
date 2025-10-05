from typing import Protocol

from ai_response_generation_v2.application.dtos.artifact import ArtifactAdmissionNotificationDTO


class MessageBrokerPublisherProtocol(Protocol):
    async def publish_new_artifact(
        self, artifact: ArtifactAdmissionNotificationDTO
    ) -> None: ...
