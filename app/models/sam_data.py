import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func

from app.db.base import Base


class SamData(Base):
    __tablename__ = "sam_data"

    sam_data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    file_id = Column(UUID(as_uuid=True), ForeignKey("files.file_id", ondelete="CASCADE"), nullable=False)

    extracted_at = Column(DateTime(timezone=True), server_default=func.now())
    extracted_type = Column(String(10), nullable=False)
    extracted_by = Column(UUID(as_uuid=True), nullable=False)

    # 🔹 Core Fields
    record_id = Column(String(50), nullable=False)
    duns_number = Column(String(50))
    status_code = Column(String(10))
    entity_type = Column(String(10))

    # 🔹 Dates
    registration_date = Column(String(20))
    expiration_date = Column(String(20))
    last_update_date = Column(String(20))
    activation_date = Column(String(20))

    # 🔹 Organization Info
    organization_name = Column(String(255), nullable=False)
    legal_business_name = Column(String(255))
    division_name = Column(String(255))

    # 🔹 Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    zip_extension = Column(String(20))
    country = Column(String(50))

    # 🔹 Business Info
    congressional_district = Column(String(20))
    business_start_date = Column(String(20))
    fiscal_year_end = Column(String(20))
    website = Column(String(255))

    __table_args__ = (
        CheckConstraint("extracted_type IN('admin', 'user')", name="check_extracted_type"),

        Index("idx_sam_data_file", "file_id"),
        Index("idx_extracted_at", "extracted_at"),
        Index("idx_org_name", "organization_name"),
        Index("idx_state", "state"),
    )