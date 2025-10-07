from __future__ import annotations

from dataclasses import dataclass, field

from ai_response_generation_v2.config.base import Settings


@dataclass(slots=True)
class AICatalogService:
    settings: Settings = field(default_factory=Settings)

    def list_models(self) -> dict:
        chat_models = [
            model.strip()
            for model in self.settings.openai_available_models.split(",")
            if model.strip()
        ]
        return {
            "providers": [
                {
                    "name": "openai",
                    "instruments": [
                        {
                            "name": "chat",
                            "models": chat_models,
                        }
                    ],
                }
            ]
        }

    def default_provider(self) -> str:
        return self.settings.enabled_ai_providers[0]

