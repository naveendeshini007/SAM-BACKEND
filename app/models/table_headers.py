from sqlalchemy import Boolean, Index, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class TableHeaders(Base):
    __tablename__ = "table_headers"

    table_header_id: Mapped[int]  = mapped_column(primary_key=True, autoincrement=True)
    table_name: Mapped[str]  = mapped_column(String(100), nullable=False)
    column_name: Mapped[str]  = mapped_column(String(100), nullable=False)
    display_name: Mapped[str]  = mapped_column(String(150), nullable=False)
    order: Mapped[int]  = mapped_column(SmallInteger, nullable=False, default=0)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("table_name", "column_name", name="uq_table_column"),
        Index("idx_table_columns_table_name", "table_name",
              postgresql_where=("is_visible = TRUE")),
    )