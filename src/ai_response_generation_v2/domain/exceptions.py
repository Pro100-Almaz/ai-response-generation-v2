from typing import final


@final
class InvalidMaterialException(Exception): ...


@final
class InvalidEraException(Exception): ...


@final
class ConversationNotFoundException(Exception): ...


@final
class MessageNotFoundException(Exception): ...
