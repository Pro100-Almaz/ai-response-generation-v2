from __future__ import annotations

from dataclasses import dataclass

from ai_response_generation_v2.application.use_cases.model_catalog import ListAIModelCatalogUseCase


@dataclass(slots=True)
class AICatalogService:
    list_catalog_use_case: ListAIModelCatalogUseCase

    async def list_models(self) -> dict:
        providers = await self.list_catalog_use_case.execute()
        payload_providers: list[dict] = []
        for provider in providers:
            provider_payload = {
                "id": provider.id,
                "name": provider.name,
                "display_name": provider.display_name,
                "description": provider.description,
                "avatar_url": provider.avatar_url,
                "types": [],
            }
            for model_type in provider.types:
                type_payload = {
                    "id": model_type.id,
                    "identifier": model_type.identifier,
                    "display_name": model_type.display_name,
                    "description": model_type.description,
                    "avatar_url": model_type.avatar_url,
                    "models": [],
                }
                for model in model_type.models:
                    type_payload["models"].append(
                        {
                            "id": model.id,
                            "name": model.name,
                            "display_name": model.display_name,
                            "description": model.description,
                            "avatar_url": model.avatar_url,
                        }
                    )
                provider_payload["types"].append(type_payload)

            payload_providers.append(provider_payload)

        return {"providers": payload_providers}

