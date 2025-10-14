from dishka import Provider

from ai_response_generation_v2.config.ioc.providers import (
    AIProvider,
    AuthorizationProvider,
    BalanceProvider,
    BrokerProvider,
    CacheProvider,
    DatabaseProvider,
    HTTPClientProvider,
    MapperProvider,
    OpenAIProvider,
    RepositoryProvider,
    ServiceProvider,
    SettingsProvider,
    UnitOfWorkProvider,
    UseCaseProvider,
)


def get_providers() -> list[Provider]:
    return [
        SettingsProvider(),
        DatabaseProvider(),
        HTTPClientProvider(),
        BrokerProvider(),
        RepositoryProvider(),
        UnitOfWorkProvider(),
        ServiceProvider(),
        MapperProvider(),
        CacheProvider(),
        OpenAIProvider(),
        AIProvider(),
        AuthorizationProvider(),
        BalanceProvider(),
        UseCaseProvider(),
    ]
