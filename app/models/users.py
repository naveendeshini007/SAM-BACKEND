import uuid

from sqlalchemy import Boolean, DateTime, Index, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_by_admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("admins.admin_id", ondelete="RESTRICT"), nullable=False
    )
    last_login_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
        Index("idx_users_created_by", "created_by_admin_id"),
    )

    created_by_admin = relationship("Admin")
