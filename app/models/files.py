import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, Text, CheckConstraint, Index, Integer
from sqlalchemy.sql import func

from app.db.base import Base

class Files(Base):
    __tablename__ = "files"

    file_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    file_version = Column(String(50), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_month_year = Column(Integer, nullable=False)

    processor_type = Column(String(10), nullable=False)
    processor_id = Column(UUID(as_uuid=True), nullable=False)

    processed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    notes = Column(Text, nullable=True)

    #Check Constraints
    __table_args__ = (
        CheckConstraint("file_month_year BETWEEN 21000 AND 122099", name="check_file_month_year"),
        CheckConstraint("processor_type IN ('admin','user')", name="check_processor_type"),

        Index("unique_file_name_month_year","file_name", "file_month_year", unique=True),

        Index("idx_downloads_file", "file_id"),
        Index("idx_files_processor", "processor_type", "processor_id"),
        Index("idx_processed_time", "processed_at"),
        Index("idx_files_month_year", "file_month_year"),
    )