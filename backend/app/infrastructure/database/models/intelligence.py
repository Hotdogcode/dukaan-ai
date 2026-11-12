import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin


class AIConversation(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Conversational session between a merchant staff member and DukaanAI."""
    __tablename__ = "ai_conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    session_title: Mapped[str | None] = mapped_column(String(120), nullable=True)

    messages: Mapped[list["AIMessage"]] = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan")
    actions: Mapped[list["AIAction"]] = relationship("AIAction", back_populates="conversation", cascade="all, delete-orphan")


class AIMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Single natural language utterance or assistant response."""
    __tablename__ = "ai_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False)  # USER, ASSISTANT, SYSTEM
    raw_utterance: Mapped[str] = mapped_column(Text, nullable=False)
    intent_detected: Mapped[str | None] = mapped_column(String(60), nullable=True)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    structured_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    conversation: Mapped["AIConversation"] = relationship("AIConversation", back_populates="messages")


class AIAction(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """
    Structured action draft proposed by the AI Assistant.
    Requires human confirmation prior to execution by application services.
    """
    __tablename__ = "ai_actions"

    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # RECORD_SALE, RECORD_EXPENSE, RECORD_PURCHASE, CUSTOMER_CREDIT
    proposed_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PROPOSED", nullable=False)  # PROPOSED, USER_CONFIRMED, USER_REJECTED, EXECUTED, FAILED
    executed_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    confirmed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped["AIConversation"] = relationship("AIConversation", back_populates="actions")
