import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func

from app.db.base import Base

class SamData(Base):
    __tablename__ = "sam_data"

    sam_data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    file_id = Column(UUID(as_uuid=True), ForeignKey("files.file_id", ondelete="CASCADE"), nullable=False)
    extracted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    extracted_type = Column(String(10), nullable=False)
    extracted_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Temporary Columns (C1-C13)
    C1 = Column(String(50), nullable=True)
    C2 = Column(String(120), nullable=True)
    C3 = Column(String(100), nullable=True)
    C4 = Column(String(100), nullable=True)
    C5 = Column(String(20), nullable=True)
    C6 = Column(String(40), nullable=True)

    C7 = Column(Numeric(14, 2), nullable=True)
    C8 = Column(Numeric(14, 2), nullable=True)
    C9 = Column(Numeric(14, 2), nullable=True)
    C10 = Column(Numeric(14, 2), nullable=True)

    C11 = Column(Integer, nullable=True)
    C12 = Column(Integer, nullable=True)
    C13 = Column(Integer, nullable=True)

    #Check Constraints
    __table_args__ = (
        CheckConstraint("extracted_type IN('admin', 'user')", name="check_extracted_type"),

        Index("idx_sam_data_file", "file_id"),
        Index("idx_extracted_at", "extracted_at"),
    )
    









