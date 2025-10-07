from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from faststream.kafka import KafkaBroker
from httpx import AsyncClient
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from ai_response_generation_v2.application.mappers import ArtifactMapper, ConversationMapper
from ai_response_generation_v2.application.use_cases.get_artifact import GetArtifactUseCase
from ai_response_generation_v2.application.use_cases.conversation_use_cases import (
    AddMessageUseCase,
    CreateConversationUseCase,
    GetConversationHistoryUseCase,
    ListConversationsUseCase,
)
from ai_response_generation_v2.application.use_cases.chat_use_cases import GenerateResponseUseCase
from ai_response_generation_v2.config.base import Settings
from ai_response_generation_v2.infrastructures.broker.publisher import KafkaPublisher
from ai_response_generation_v2.infrastructures.cache.redis_client import RedisCacheClient
from ai_response_generation_v2.infrastructures.db.repositories.artifact import ArtifactRepositorySQLAlchemy
from ai_response_generation_v2.infrastructures.db.repositories.conversation import (
    ConversationRepositorySQLAlchemy,
    MessageRepositorySQLAlchemy,
)
from ai_response_generation_v2.infrastructures.db.session import create_engine, get_session_factory
from ai_response_generation_v2.infrastructures.db.uow import UnitOfWorkSQLAlchemy
from ai_response_generation_v2.infrastructures.http.clients import (
    ExternalMuseumAPIClient, PublicCatalogAPIClient
)
from ai_response_generation_v2.infrastructures.ai.factory import AIChatClientFactory
from ai_response_generation_v2.infrastructures.auth.service import MonolithAuthorizationService
from ai_response_generation_v2.infrastructures.mappers.artifact import InfrastructureArtifactMapper
from ai_response_generation_v2.infrastructures.openai.chat_client import OpenAIChatClient


class SettingsProvider(Provider):
    @provide(scope=Scope.APP)
    def get_settings(self) -> Settings:
        return Settings()


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_session_factory(
        self, settings: Settings
    ) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
        engine = create_engine(str(settings.database_url), is_echo=settings.debug)
        session_factory = get_session_factory(engine)
        try:
            yield session_factory
        finally:
            await engine.dispose()

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session


class HTTPClientProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_http_client(self, settings: Settings) -> AsyncIterator[AsyncClient]:
        client = AsyncClient(timeout=settings.http_timeout)
        try:
            yield client
        finally:
            await client.aclose()


class BrokerProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_broker(self, settings: Settings) -> AsyncIterator[KafkaBroker]:
        broker = KafkaBroker(settings.broker_url)
        try:
            yield broker
        finally:
            await broker.close()


class RepositoryProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_artifact_repository(
        self, session: AsyncSession
    ) -> ArtifactRepositorySQLAlchemy:
        return ArtifactRepositorySQLAlchemy(session=session)

    @provide(scope=Scope.REQUEST)
    def get_conversation_repository(
        self, session: AsyncSession
    ) -> ConversationRepositorySQLAlchemy:
        return ConversationRepositorySQLAlchemy(session=session)

    @provide(scope=Scope.REQUEST)
    def get_message_repository(
        self, session: AsyncSession
    ) -> MessageRepositorySQLAlchemy:
        return MessageRepositorySQLAlchemy(session=session)


class UnitOfWorkProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_unit_of_work(
        self,
        session: AsyncSession,
        repository: ArtifactRepositorySQLAlchemy,
        conversation_repository: ConversationRepositorySQLAlchemy,
        message_repository: MessageRepositorySQLAlchemy,
    ) -> UnitOfWorkSQLAlchemy:
        return UnitOfWorkSQLAlchemy(
            session=session,
            repository=repository,
            conversations=conversation_repository,
            messages=message_repository,
        )


class ServiceProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_external_museum_api_client(
        self,
        client: AsyncClient,
        settings: Settings,
        infrastructure_mapper: InfrastructureArtifactMapper,
    ) -> ExternalMuseumAPIClient:
        return ExternalMuseumAPIClient(
            base_url=settings.external_api_base_url, 
            client=client,
            mapper=infrastructure_mapper,
        )

    @provide(scope=Scope.REQUEST)
    def get_public_catalog_api_client(
        self,
        client: AsyncClient,
        settings: Settings,
        infrastructure_mapper: InfrastructureArtifactMapper,
    ) -> PublicCatalogAPIClient:
        return PublicCatalogAPIClient(
            base_url=settings.catalog_api_base_url,
            client=client,
            mapper=infrastructure_mapper,
        )

    @provide(scope=Scope.REQUEST)
    def get_message_broker(
        self, 
        broker: KafkaBroker,
        infrastructure_mapper: InfrastructureArtifactMapper,
    ) -> KafkaPublisher:
        return KafkaPublisher(
            broker=broker,
            mapper=infrastructure_mapper,
        )


class MapperProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_artifact_mapper(self) -> ArtifactMapper:
        return ArtifactMapper()

    @provide(scope=Scope.REQUEST)
    def get_infrastructure_artifact_mapper(self) -> InfrastructureArtifactMapper:
        return InfrastructureArtifactMapper()

    @provide(scope=Scope.REQUEST)
    def get_conversation_mapper(self) -> ConversationMapper:
        return ConversationMapper()


class CacheProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_cache_service(
        self, settings: Settings
    ) -> AsyncIterator[RedisCacheClient]:
        redis_client = await redis.from_url(
            str(settings.redis_url),
            encoding="utf-8",
            decode_responses=False,
            health_check_interval=30,
            max_connections=10,
            retry_on_timeout=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        cache_service = RedisCacheClient(
            client=redis_client, ttl=settings.redis_cache_ttl
        )
        try:
            yield cache_service
        finally:
            await cache_service.close()


class UseCaseProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_register_artifact_use_case(
        self,
        uow: UnitOfWorkSQLAlchemy,
        museum_api_client: ExternalMuseumAPIClient,
        catalog_api_client: PublicCatalogAPIClient,
        message_broker: KafkaPublisher,
        artifact_mapper: ArtifactMapper,
        cache_client: RedisCacheClient,
    ) -> GetArtifactUseCase:
        return GetArtifactUseCase(
            uow=uow,
            museum_api_client=museum_api_client,
            catalog_api_client=catalog_api_client,
            message_broker=message_broker,
            artifact_mapper=artifact_mapper,
            cache_client=cache_client,
        )

    @provide(scope=Scope.REQUEST)
    def get_create_conversation_use_case(
        self,
        uow: UnitOfWorkSQLAlchemy,
        mapper: ConversationMapper,
    ) -> CreateConversationUseCase:
        return CreateConversationUseCase(uow=uow, mapper=mapper)

    @provide(scope=Scope.REQUEST)
    def get_list_conversations_use_case(
        self,
        conversation_repository: ConversationRepositorySQLAlchemy,
        mapper: ConversationMapper,
    ) -> ListConversationsUseCase:
        return ListConversationsUseCase(conversations=conversation_repository, mapper=mapper)

    @provide(scope=Scope.REQUEST)
    def get_get_conversation_history_use_case(
        self,
        conversation_repository: ConversationRepositorySQLAlchemy,
        message_repository: MessageRepositorySQLAlchemy,
        mapper: ConversationMapper,
    ) -> GetConversationHistoryUseCase:
        return GetConversationHistoryUseCase(
            conversations=conversation_repository,
            messages=message_repository,
            mapper=mapper,
        )

    @provide(scope=Scope.REQUEST)
    def get_add_message_use_case(
        self,
        uow: UnitOfWorkSQLAlchemy,
        mapper: ConversationMapper,
    ) -> AddMessageUseCase:
        return AddMessageUseCase(uow=uow, mapper=mapper)

    @provide(scope=Scope.REQUEST)
    def get_generate_response_use_case(
        self,
        ai_client_factory: AIChatClientFactory,
    ) -> GenerateResponseUseCase:
        return GenerateResponseUseCase(ai_client_factory=ai_client_factory)


class OpenAIProvider(Provider):
    @provide(scope=Scope.APP)
    def get_openai_client(self, settings: Settings) -> OpenAIChatClient:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        return OpenAIChatClient(
            client=client,
            default_model=settings.openai_default_model,
            default_temperature=settings.openai_temperature,
            default_max_tokens=settings.openai_max_tokens,
        )


class AIProvider(Provider):
    @provide(scope=Scope.APP)
    def get_ai_client_factory(
        self,
        openai_client: OpenAIChatClient,
    ) -> AIChatClientFactory:
        factory = AIChatClientFactory()
        factory.register_client("openai", "chat", openai_client)
        return factory


class AuthorizationProvider(Provider):
    @provide(scope=Scope.APP)
    def get_monolith_authorizer(
        self,
        settings: Settings,
        http_client: AsyncClient,
    ) -> MonolithAuthorizationService:
        with open(settings.monolith_public_key_path, "r", encoding="utf-8") as key_file:
            public_key = key_file.read()

        return MonolithAuthorizationService(
            base_url=settings.monolith_base_url,
            audience=settings.monolith_auth_audience,
            timeout=settings.monolith_auth_timeout,
            client=http_client,
            public_key=public_key,
        )
