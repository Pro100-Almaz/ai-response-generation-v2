from typing import Protocol

from ai_response_generation_v2.application.interfaces.repositories import (
    ArtifactRepositoryProtocol,
    ConversationRepositoryProtocol,
    MessageRepositoryProtocol,
)


class UnitOfWorkProtocol(Protocol):
    repository: ArtifactRepositoryProtocol
    conversations: ConversationRepositoryProtocol
    messages: MessageRepositoryProtocol

    async def __aenter__(self) -> "UnitOfWorkProtocol": ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
