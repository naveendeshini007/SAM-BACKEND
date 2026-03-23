import uuid

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class AuthEvents(Base):
    __tablename__ = "auth_events"

    auth_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    app_user_type: Mapped[str] = mapped_column(String(10), nullable=False)
    app_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    happened_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    related_event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("idx_auth_events_app_user_type", "app_user_type"),
        Index("idx_auth_events_app_user_id", "app_user_id"),
        Index("idx_auth_events_happened_at", "happened_at"),
        Index("idx_auth_events_type", "event_type"),
    )
