from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from ai_response_generation_v2.application.interfaces.ai import (
    AIChatClientFactoryProtocol,
    AIChatClientProtocol,
)


@dataclass(slots=True)
class AIChatClientFactory(AIChatClientFactoryProtocol):
    clients: Dict[str, Dict[str, AIChatClientProtocol]] = field(default_factory=dict)

    def register_client(self, provider: str, instrument: str, client: AIChatClientProtocol) -> None:
        provider_key = provider.lower()
        instrument_key = instrument.lower()
        self.clients.setdefault(provider_key, {})[instrument_key] = client

    def get_client(self, provider: str, instrument: str) -> AIChatClientProtocol:
        provider_key = provider.lower()
        instrument_key = instrument.lower()
        if provider_key not in self.clients:
            raise ValueError(f"No AI provider registered under '{provider}'")
        instruments = self.clients[provider_key]
        if instrument_key not in instruments:
            raise ValueError(
                f"Provider '{provider}' does not support instrument '{instrument}'"
            )
        return instruments[instrument_key]

