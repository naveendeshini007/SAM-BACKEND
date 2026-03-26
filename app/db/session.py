from __future__ import annotations

from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

_STAGING_COL_COUNT = 142  # must match app/services/extractor.py / normalize_sam_pipe_line()
_STAGING_COLS = [f"col{i}" for i in range(1, _STAGING_COL_COUNT + 1)]
_STAGING_COL_LIST_SQL = ", ".join(_STAGING_COLS)


async def init_db(session: AsyncSession) -> None:
    """Create pipeline tables if they don't exist."""
    staging_cols_sql = ", ".join([f"{c} TEXT" for c in _STAGING_COLS])

    await session.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS sam_staging_raw (
                sam_data_id UUID NOT NULL DEFAULT gen_random_uuid(),
                file_id UUID,
                extracted_at TIMESTAMPTZ,
                extractor_type VARCHAR(10),
                extracted_by UUID,
                {staging_cols_sql},
                file_date DATE
            );
            """
        )
    )
    await session.execute(
        text(
            """
            CREATE EXTENSION IF NOT EXISTS pgcrypto
            """
        )
    )
    await session.execute(
        text(
            """
            ALTER TABLE sam_staging_raw
            ADD COLUMN IF NOT EXISTS sam_data_id UUID
            """
        )
    )
    await session.execute(
        text(
            """
            UPDATE sam_staging_raw
            SET sam_data_id = gen_random_uuid()
            WHERE sam_data_id IS NULL
            """
        )
    )
    await session.execute(
        text(
            """
            ALTER TABLE sam_staging_raw
            ALTER COLUMN sam_data_id SET DEFAULT gen_random_uuid()
            """
        )
    )
    await session.execute(
        text(
            """
            ALTER TABLE sam_staging_raw
            ALTER COLUMN sam_data_id SET NOT NULL
            """
        )
    )
    await session.execute(
        text(
            """
            ALTER TABLE sam_staging_raw
            ADD COLUMN IF NOT EXISTS file_id UUID
            """
        )
    )
    await session.execute(
        text(
            """
            ALTER TABLE sam_staging_raw
            ADD COLUMN IF NOT EXISTS extracted_at TIMESTAMPTZ
            """
        )
    )
    await session.execute(
        text(
            """
            ALTER TABLE sam_staging_raw
            ADD COLUMN IF NOT EXISTS extractor_type VARCHAR(10)
            """
        )
    )
    await session.execute(
        text(
            """
            ALTER TABLE sam_staging_raw
            ADD COLUMN IF NOT EXISTS extracted_by UUID
            """
        )
    )
    await session.execute(
        text(
            """
            ALTER TABLE sam_staging_raw
            ADD COLUMN IF NOT EXISTS file_date DATE
            """
        )
    )

    await session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS sam_entities (
                uei TEXT,
                entity_name TEXT,
                city TEXT,
                state TEXT,
                naics_code TEXT,
                entity_structure TEXT,
                file_date DATE,
                PRIMARY KEY (uei, file_date)
            );
            """
        )
    )
    await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    await session.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_sam_entities_file_date_uei
            ON sam_entities (file_date DESC, uei)
            """
        )
    )
    await session.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_sam_entities_state
            ON sam_entities (state)
            """
        )
    )
    await session.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_sam_entities_entity_name_trgm
            ON sam_entities USING gin (entity_name gin_trgm_ops)
            """
        )
    )
    await session.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_sam_entities_uei_trgm
            ON sam_entities USING gin (uei gin_trgm_ops)
            """
        )
    )
    await session.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_sam_staging_raw_file_date_col1
            ON sam_staging_raw (file_date, col1)
            """
        )
    )
    await session.execute(
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_sam_staging_raw_sam_data_id
            ON sam_staging_raw (sam_data_id)
            """
        )
    )
    await session.execute(
        text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'pk_sam_staging_raw_sam_data_id'
                ) THEN
                    ALTER TABLE sam_staging_raw
                    ADD CONSTRAINT pk_sam_staging_raw_sam_data_id
                    PRIMARY KEY USING INDEX uq_sam_staging_raw_sam_data_id;
                END IF;
            END
            $$;
            """
        )
    )
    await session.commit()


async def copy_to_staging(
    session: AsyncSession,
    file_path: str,
    file_date: date,
    *,
    batch_size: int = 50000,
    max_rows: int | None = None,
) -> None:
    """
    Bulk-load using PostgreSQL COPY for higher throughput than INSERT batches.
    """
    async_conn = await session.connection()
    raw_conn = await async_conn.get_raw_connection()
    driver_conn = raw_conn.driver_connection
    column_names = _STAGING_COLS + ["file_date"]

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

            batch.append(tuple(parts + [file_date]))
            rows_loaded += 1

            if max_rows is not None and rows_loaded >= max_rows:
                break

            if len(batch) >= batch_size:
                await driver_conn.copy_records_to_table(
                    "sam_staging_raw",
                    records=batch,
                    columns=column_names,
                )
                batch.clear()

    if batch:
        await driver_conn.copy_records_to_table(
            "sam_staging_raw",
            records=batch,
            columns=column_names,
        )

    await session.commit()


async def delete_staging_for_date(session: AsyncSession, file_date: date) -> int:
    """Delete staging rows for a given month and return deleted row count."""
    res = await session.execute(
        text(
            """
            DELETE FROM sam_staging_raw
            WHERE file_date = :file_date
            """
        ),
        {"file_date": file_date},
    )
    await session.commit()
    return int(res.rowcount or 0)


async def is_entities_loaded(session: AsyncSession, file_date: date) -> bool:
    """
    Returns True if `sam_entities` already has rows for this `file_date`.

    Used to make the pipeline idempotent per month, so changing LIMIT_ROWS
    later does not change DB contents.
    """
    res = await session.execute(
        text(
            """
            SELECT 1
            FROM sam_entities
            WHERE file_date = :file_date
            LIMIT 1
            """
        ),
        {"file_date": file_date},
    )
    return res.scalar_one_or_none() is not None


async def delete_entities_for_date(session: AsyncSession, file_date: date) -> int:
    """Delete existing entities for a given month and return deleted row count."""
    res = await session.execute(
        text(
            """
            DELETE FROM sam_entities
            WHERE file_date = :file_date
            """
        ),
        {"file_date": file_date},
    )
    await session.commit()
    return int(res.rowcount or 0)


async def get_staging_count(session: AsyncSession, file_date: date) -> int:
    res = await session.execute(
        text("SELECT COUNT(*) FROM sam_staging_raw WHERE file_date = :file_date"),
        {"file_date": file_date},
    )
    return int(res.scalar_one())


async def upsert(session: AsyncSession, file_date: date) -> None:
    """Insert distinct entities from staging into the final table."""
    await session.execute(
        text(
            """
            INSERT INTO sam_entities (
                uei,
                entity_name,
                city,
                state,
                naics_code,
                entity_structure,
                file_date
            )
            SELECT DISTINCT ON (col1)
                col1,     -- UEI
                col12,    -- NAME
                col18,    -- CITY
                col19,    -- STATE
                col33,    -- NAICS
                col28,    -- STRUCTURE
                :file_date
            FROM sam_staging_raw
            WHERE file_date = :file_date
            ORDER BY col1
            ON CONFLICT (uei, file_date)
            DO UPDATE SET entity_name = EXCLUDED.entity_name;
            """
        ),
        {"file_date": file_date},
    )
    await session.commit()
    