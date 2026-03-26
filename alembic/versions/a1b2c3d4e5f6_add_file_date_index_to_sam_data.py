"""add file_date index to sam_data

Revision ID: a1b2c3d4e5f6
Revises: 8f3d1a86458a
Create Date: 2026-03-26 20:00:00.000000

Without an index on file_date, the pipeline's DELETE and COUNT queries do a
full sequential scan of the entire sam_data table – which can be millions of
rows.  This index makes both operations O(log n) instead of O(n).
"""
from typing import Sequence, Union

from alembic import op


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "8f3d1a86458a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # CONCURRENTLY avoids a full table lock on large tables.
    # Alembic runs this outside a transaction block (transaction_per_migration
    # must be False or the statement must be isolated) – if you see an error,
    # run the CREATE INDEX manually in psql.
    op.create_index(
        "idx_sam_data_file_date",
        "sam_data",
        ["file_date"],
        unique=False,
        postgresql_concurrently=True,
    )


def downgrade() -> None:
    op.drop_index("idx_sam_data_file_date", table_name="sam_data")
