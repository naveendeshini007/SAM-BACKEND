from __future__ import annotations

import uuid
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.sam_data import (
    SAM_PIPE_COLUMN_COUNT,
    SAM_PIPE_COLUMNS,
)

engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

_STAGING_COL_COUNT = SAM_PIPE_COLUMN_COUNT
_STAGING_COLS = SAM_PIPE_COLUMNS


async def init_db(session: AsyncSession) -> None:
    """Ensure required DB extensions exist."""
    await session.execute(
        text(
            """
            CREATE EXTENSION IF NOT EXISTS pgcrypto
            """
        )
    )
    await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    await session.commit()


async def copy_to_staging(
    session: AsyncSession,
    file_path: str,
    file_date: date,
    *,
    batch_size: int = 200000,
    max_rows: int | None = None,
) -> None:
    """
    Bulk-load using PostgreSQL COPY for higher throughput than INSERT batches.
    """
    async_conn = await session.connection()
    await session.execute(text("SET LOCAL synchronous_commit TO OFF"))
    raw_conn = await async_conn.get_raw_connection()
    driver_conn = raw_conn.driver_connection
    column_names = [
        "sam_data_id",
        "record_id",
        "organization_name",
        "extracted_type",
    ] + _STAGING_COLS + ["file_date"]

    batch: list[tuple[str, ...]] = []
    rows_loaded = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line:
                continue

            parts = line.split("|")
            if len(parts) < _STAGING_COL_COUNT:
                parts.extend([""] * (_STAGING_COL_COUNT - len(parts)))
            elif len(parts) > _STAGING_COL_COUNT:
                parts = parts[: _STAGING_COL_COUNT - 1] + [
                    "|".join(parts[_STAGING_COL_COUNT - 1 :])
                ]

            record_id = parts[0] if len(parts) > 0 else ""
            organization_name = parts[11] if len(parts) > 11 else ""
            extracted_type = "admin"
            batch.append(
                tuple(
                    [uuid.uuid4(), record_id, organization_name, extracted_type]
                    + parts
                    + [file_date]
                )
            )
            rows_loaded += 1

            if max_rows is not None and rows_loaded >= max_rows:
                break

            if len(batch) >= batch_size:
                await driver_conn.copy_records_to_table(
                    "sam_data",
                    records=batch,
                    columns=column_names,
                )
                batch.clear()

    if batch:
        await driver_conn.copy_records_to_table(
            "sam_data",
            records=batch,
            columns=column_names,
        )

    await session.commit()


async def delete_staging_for_date(session: AsyncSession, file_date: date) -> int:
    """Delete staging rows for a given month and return deleted row count."""
    res = await session.execute(
        text(
            """
            DELETE FROM sam_data
            WHERE file_date = :file_date
            """
        ),
        {"file_date": file_date},
    )
    await session.commit()
    return int(res.rowcount or 0)


async def get_staging_count(session: AsyncSession, file_date: date) -> int:
    res = await session.execute(
        text("SELECT COUNT(*) FROM sam_data WHERE file_date = :file_date"),
        {"file_date": file_date},
    )
    return int(res.scalar_one())
