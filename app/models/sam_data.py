import uuid

from sqlalchemy import DateTime, Index, Integer, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey

from app.db.base import Base


class SamData(Base):
    __tablename__ = "sam_data"

    sam_data_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("files.file_id", ondelete="CASCADE"), nullable=False)
    extracted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True, server_default=func.now())
    extractor_type: Mapped[str] = mapped_column(String(10), nullable=False)
    extracted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    C1: Mapped[str | None] = mapped_column(String(50), nullable=True)
    C2: Mapped[str | None] = mapped_column(String(120), nullable=True)
    C3: Mapped[str | None] = mapped_column(String(100), nullable=True)
    C4: Mapped[str | None] = mapped_column(String(100), nullable=True)
    C5: Mapped[str | None] = mapped_column(String(20), nullable=True)
    C6: Mapped[str | None] = mapped_column(String(40), nullable=True)
    C7: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    C8: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    C9: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    C10: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    C11: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    C12: Mapped[int | None] = mapped_column(Integer, nullable=True)
    C13: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_extracted_file", "file_id"),
        Index("idx_extracted_extracted_at", "extracted_at"),
    )
