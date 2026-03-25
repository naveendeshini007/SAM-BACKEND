import uuid

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Files(Base):
    __tablename__ = "files"

    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_month_year: Mapped[int] = mapped_column(Integer, nullable=False)
    processor_type: Mapped[str] = mapped_column(String(10), nullable=False)
    processor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    processed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True, server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_downloads_file", "file_id"),
        Index("idx_files_processor", "processor_type", "processor_id"),
        Index("idx_processed_time", "processed_at"),
        Index("idx_files_month_year", "file_month_year"),
        UniqueConstraint("file_name", "file_month_year", name="unique_file_name_month_year"),
        CheckConstraint("file_month_year >= 12000 AND file_month_year <= 122099", name="chk_file_month_year_range"),
    )
