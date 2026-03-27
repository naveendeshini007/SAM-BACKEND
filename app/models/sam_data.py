import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, CheckConstraint, Index,Integer,Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column


from app.db.base import Base

SAM_PIPE_COLUMN_COUNT = 142
SAM_PIPE_COLUMNS = [f"col{i}" for i in range(1, SAM_PIPE_COLUMN_COUNT + 1)]


class SamData(Base):
    __tablename__ = "sam_data"

    sam_data_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("files.file_id", ondelete="CASCADE"), nullable=True)

    extracted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), 
    server_default=func.now(),nullable=True)
    extracted_type: Mapped[str] = mapped_column(String(10), nullable=True)
    extracted_by: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    nullable=True)

    # Core Fields
    record_id: Mapped[str] = mapped_column(String(50), nullable=False)
    duns_number: Mapped[str | None] = mapped_column(String(50))
    status_code: Mapped[str | None] = mapped_column(String(10))
    entity_type: Mapped[str | None] = mapped_column(String(10))

    # Dates
    registration_date: Mapped[str | None] = mapped_column(String(20))
    expiration_date: Mapped[str | None] = mapped_column(String(20))
    last_update_date: Mapped[str | None] = mapped_column(String(20))
    activation_date: Mapped[str | None] = mapped_column(String(20))

    # Organization Info
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_business_name: Mapped[str | None] = mapped_column(String(255))
    division_name: Mapped[str | None] = mapped_column(String(255))

    # Address
    address_line1: Mapped[str | None] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(50))
    zip_code: Mapped[str | None] = mapped_column(String(20))
    zip_extension: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str | None] = mapped_column(String(50))

    # Business Info
    congressional_district: Mapped[str | None] = mapped_column(String(20))
    business_start_date: Mapped[str | None] = mapped_column(String(20))
    fiscal_year_end: Mapped[str | None] = mapped_column(String(20))
    website: Mapped[str | None] = mapped_column(String(255))
    file_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    # Keep existing named fields unchanged; add raw SAM fields additionally.
    for i in range(1, 143):
        locals()[f"col{i}"] = Column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("extracted_type IN('admin', 'user')", name="check_extracted_type"),

        Index("idx_sam_data_file", "file_id"),
        Index("idx_extracted_at", "extracted_at"),
        Index("idx_org_name", "organization_name"),
        Index("idx_state", "state"),
    )
