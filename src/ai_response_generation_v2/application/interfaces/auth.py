from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping


class AuthorizationServiceProtocol(ABC):
    @abstractmethod
    async def authorize(self, token: str | None) -> Mapping[str, object]: ...


