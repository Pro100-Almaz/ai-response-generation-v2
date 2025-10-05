from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ai_response_generation_v2.domain.entities import ConversationEntity, MessageEntity
from ai_response_generation_v2.infrastructures.db.models.artifact import mapper_registry


@mapper_registry.mapped
class ConversationModel:
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<ConversationModel(id={self.id!s}, user_id={self.user_id}, "
            f"title={self.title!r})>"
        )

    def to_entity(self) -> ConversationEntity:
        return ConversationEntity(
            id=self.id,
            user_id=self.user_id,
            title=self.title,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(
        cls: type["ConversationModel"], entity: ConversationEntity
    ) -> "ConversationModel":
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            title=entity.title,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


@mapper_registry.mapped
class MessageModel:
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_id", "conversation_id"),
        Index("ix_messages_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )
    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(length=32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str | None] = mapped_column(String(length=128), nullable=True)
    ai_type: Mapped[str] = mapped_column(String(length=64), nullable=False, default="unknown")
    message_type: Mapped[str] = mapped_column(String(length=32), nullable=False, default="text")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<MessageModel(id={self.id!s}, conversation_id={self.conversation_id!s}, "
            f"role={self.role!r})>"
        )

    def to_entity(self) -> MessageEntity:
        return MessageEntity(
            id=self.id,
            conversation_id=self.conversation_id,
            role=self.role,  # type: ignore[arg-type]
            content=self.content,
            model=self.model,
            ai_type=self.ai_type,  # type: ignore[arg-type]
            message_type=self.message_type,  # type: ignore[arg-type]
            created_at=self.created_at,
        )

    @classmethod
    def from_entity(cls: type["MessageModel"], entity: MessageEntity) -> "MessageModel":
        return cls(
            id=entity.id,
            conversation_id=entity.conversation_id,
            role=entity.role,
            content=entity.content,
            model=entity.model,
            ai_type=entity.ai_type,
            message_type=entity.message_type,
            created_at=entity.created_at,
        )

