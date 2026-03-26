from __future__ import annotations

import asyncio
import logging
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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine – connection pool tuned for pipeline workloads.
# pool_pre_ping validates connections before use, avoiding stale-connection
# errors on long-idle pipelines.
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

_STAGING_COL_COUNT = SAM_PIPE_COLUMN_COUNT
_STAGING_COLS = SAM_PIPE_COLUMNS

# 8 MB read buffer – reduces system calls significantly for multi-GB .dat files.
_FILE_BUFFER_SIZE = 8 * 1024 * 1024

# One-time flag so extension setup is not repeated on every pipeline run.
_DB_READY = False


async def init_db(session: AsyncSession) -> None:
    """Ensure required DB extensions exist. Runs only once per process."""
    global _DB_READY
    if _DB_READY:
        return
    await session.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    await session.commit()
    _DB_READY = True


# ---------------------------------------------------------------------------
# FAST PATH – single-pass producer/consumer streaming load
# ---------------------------------------------------------------------------
async def stream_load_to_staging(
    session: AsyncSession,
    dat_path: str,
    file_date: date,
    *,
    batch_size: int = 200_000,
    max_rows: int | None = None,
) -> int:
    """
    Parse raw .dat file and stream records directly into Postgres COPY in one
    pass – no intermediate clean file is written.

    Architecture (producer-consumer):
    ┌─────────────────────────┐       asyncio.Queue        ┌──────────────────────┐
    │  Parser thread (pool)   │ ──── [batch, batch, ...] ──▶  Event loop (COPY)   │
    │  reads + normalizes     │      backpressure (max 3)   │  asyncpg bulk insert │
    └─────────────────────────┘                             └──────────────────────┘

    Benefits over clean-file approach:
    • Eliminates one full disk read + one full disk write per run.
    • CPU-bound parsing runs in a thread while async COPY runs concurrently.
    • Queue backpressure caps memory at 3 × batch_size rows at any time.
    """
    loop = asyncio.get_running_loop()

    # Bounded queue provides backpressure: parser blocks when COPY is behind.
    queue: asyncio.Queue[list | None] = asyncio.Queue(maxsize=3)

    column_names = (
        ["sam_data_id", "record_id", "organization_name", "extracted_type"]
        + _STAGING_COLS
        + ["file_date"]
    )

    def _parse_worker() -> int:
        """
        Runs in thread pool.
        Reads, normalises, and batches rows from the raw .dat file.
        Puts completed batches into the shared queue; sends None as sentinel.
        Returns the total number of rows parsed.
        """
        batch: list = []
        rows = 0
        normalized_count = 0

        with open(dat_path, "r", encoding="utf-8", buffering=_FILE_BUFFER_SIZE) as f:
            for raw_line in f:
                # Skip SAM file header / footer rows.
                if raw_line[:3] in ("BOF", "EOF"):
                    continue
                line = raw_line.rstrip("\r\n")
                if not line:
                    continue

                parts = line.split("|")
                n = len(parts)

                # Normalize column count only when necessary.
                if n != _STAGING_COL_COUNT:
                    normalized_count += 1
                    if n < _STAGING_COL_COUNT:
                        parts.extend([""] * (_STAGING_COL_COUNT - n))
                    else:
                        parts = parts[: _STAGING_COL_COUNT - 1] + [
                            "|".join(parts[_STAGING_COL_COUNT - 1 :])
                        ]

                batch.append((
                    uuid.uuid4(),
                    parts[0],                          # record_id  (col 1)
                    parts[11] if n > 11 else "",       # organization_name (col 12)
                    "admin",                           # extracted_type
                    *parts,
                    file_date,
                ))
                rows += 1

                if max_rows is not None and rows >= max_rows:
                    break

                if len(batch) >= batch_size:
                    # Block parser when queue is full – natural backpressure.
                    asyncio.run_coroutine_threadsafe(
                        queue.put(batch), loop
                    ).result()
                    batch = []

        if batch:
            asyncio.run_coroutine_threadsafe(queue.put(batch), loop).result()

        # Sentinel: signal consumer that parsing is complete.
        asyncio.run_coroutine_threadsafe(queue.put(None), loop).result()

        if normalized_count:
            logger.warning(
                "stream_load: normalized %d rows with non-standard pipe-field counts",
                normalized_count,
            )
        return rows

    # ---- Set up raw asyncpg connection for COPY ----
    async_conn = await session.connection()
    await session.execute(text("SET LOCAL synchronous_commit TO OFF"))
    raw_conn = await async_conn.get_raw_connection()
    driver_conn = raw_conn.driver_connection

    # ---- Launch parser thread, drain queue concurrently ----
    parser_future = loop.run_in_executor(None, _parse_worker)

    while True:
        batch = await queue.get()
        if batch is None:
            break
        await driver_conn.copy_records_to_table(
            "sam_data",
            records=batch,
            columns=column_names,
        )

    rows_parsed = await parser_future
    await session.commit()
    return rows_parsed


# ---------------------------------------------------------------------------
# FALLBACK PATH – load from a pre-cleaned file (used when clean file cached)
# ---------------------------------------------------------------------------
async def copy_to_staging(
    session: AsyncSession,
    file_path: str,
    file_date: date,
    *,
    batch_size: int = 200_000,
    max_rows: int | None = None,
) -> int:
    """
    Bulk-load from an already-cleaned pipe-delimited file using PostgreSQL COPY.
    Use stream_load_to_staging for the fastest path (no intermediate file).
    Returns total rows loaded.
    """
    async_conn = await session.connection()
    await session.execute(text("SET LOCAL synchronous_commit TO OFF"))
    raw_conn = await async_conn.get_raw_connection()
    driver_conn = raw_conn.driver_connection

    column_names = (
        ["sam_data_id", "record_id", "organization_name", "extracted_type"]
        + _STAGING_COLS
        + ["file_date"]
    )

    batch: list = []
    rows_loaded = 0
    trust_rows = settings.TRUST_CLEANED_PIPE_ROWS

    with open(file_path, "r", encoding="utf-8", buffering=_FILE_BUFFER_SIZE) as f:
        for raw_line in f:
            line = raw_line.rstrip("\r\n")
            if not line:
                continue

            parts = line.split("|")
            if (not trust_rows) or len(parts) != _STAGING_COL_COUNT:
                if len(parts) < _STAGING_COL_COUNT:
                    parts.extend([""] * (_STAGING_COL_COUNT - len(parts)))
                elif len(parts) > _STAGING_COL_COUNT:
                    parts = parts[: _STAGING_COL_COUNT - 1] + [
                        "|".join(parts[_STAGING_COL_COUNT - 1 :])
                    ]

            batch.append((
                uuid.uuid4(),
                parts[0],
                parts[11] if len(parts) > 11 else "",
                "admin",
                *parts,
                file_date,
            ))
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
    return rows_loaded


async def delete_staging_for_date(session: AsyncSession, file_date: date) -> int:
    """Delete staging rows for a given month and return deleted row count."""
    res = await session.execute(
        text("DELETE FROM sam_data WHERE file_date = :file_date"),
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
