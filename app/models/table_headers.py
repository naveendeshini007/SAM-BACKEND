import uuid
from sqlalchemy import Boolean, Column, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base

class TableHeaders(Base):
    __tablename__ = "table_headers"
    table_header_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)    
    table_name = Column(String(100), unique=True, nullable=False)    
    columns_schema = Column(JSONB, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    create_datetime = Column(TIMESTAMP(timezone=True), server_default=func.now())
    update_datetime = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())