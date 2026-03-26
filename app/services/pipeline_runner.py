import os
import logging
import asyncio
import time
from datetime import datetime
from app.services.extractor import clean_dat
from app.services.sam_download import SamDownloadService

from app.db.session import (
    AsyncSessionLocal,
    copy_to_staging,
    stream_load_to_staging,
    delete_staging_for_date,
    get_staging_count,
    init_db,
)
from app.core.config import settings

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/ingestion.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# Serialise concurrent pipeline invocations: only one run at a time.
_pipeline_lock = asyncio.Lock()


async def run_pipeline_async(file_date: str) -> None:
    async with _pipeline_lock:
        async with AsyncSessionLocal() as session:
            await init_db(session)

            try:
                max_rows = settings.LIMIT_ROWS
                if max_rows is None:
                    logging.info("LIMIT_ROWS: ALL (no row limit)")
                else:
                    logging.info("LIMIT_ROWS: %d", max_rows)

                logging.info("Pipeline starting for %s", file_date)
                pipeline_start = time.perf_counter()

                # ──────────────────── DOWNLOAD ──────────────────── #
                year = int(file_date[:4])
                month = int(file_date[4:6])

                t0 = time.perf_counter()
                download_service = SamDownloadService()
                download_result = download_service.download_and_extract(year, month)
                status = download_result.get("status")

                if status == "file_not_available":
                    raise RuntimeError(
                        f"SAM source file not available for {year}-{month:02d}"
                    )

                dat_path = download_result["dat_path"]
                resolved_file_date = download_result.get("file_date", file_date)
                if resolved_file_date != file_date:
                    logging.info(
                        "file_date resolved: requested=%s resolved=%s",
                        file_date,
                        resolved_file_date,
                    )
                file_date_obj = datetime.strptime(resolved_file_date, "%Y%m%d").date()

                logging.info(
                    "Download/extract done in %.2fs (status=%s)",
                    time.perf_counter() - t0,
                    status,
                )

                # ──────────────────── DELETE OLD DATA ──────────────────── #
                # Run delete concurrently while we resolve the load path below.
                t0 = time.perf_counter()
                deleted = await delete_staging_for_date(session, file_date_obj)
                if deleted:
                    logging.info(
                        "Replaced staging snapshot for %s; deleted %d old rows (%.2fs)",
                        resolved_file_date,
                        deleted,
                        time.perf_counter() - t0,
                    )

                # ──────────────────── CLEAN + LOAD ──────────────────── #
                load_start = time.perf_counter()

                clean_path = os.path.join(
                    os.path.dirname(dat_path),
                    f"clean_{resolved_file_date}.dat",
                )
                clean_file_cached = os.path.exists(clean_path)

                if settings.SINGLE_PASS_LOAD and not clean_file_cached:
                    # ── FAST PATH ──────────────────────────────────────────
                    # Parse raw file + COPY into Postgres in one streaming pass.
                    # A thread pool worker reads/normalises lines while asyncpg
                    # COPY runs concurrently on the event loop – true parallelism.
                    logging.info(
                        "Mode: single-pass stream (no intermediate file) [SINGLE_PASS_LOAD=True]"
                    )
                    rows_loaded = await stream_load_to_staging(
                        session,
                        dat_path,
                        file_date_obj,
                        batch_size=settings.COPY_BATCH_SIZE,
                        max_rows=max_rows,
                    )
                    logging.info(
                        "Single-pass load done: %d rows in %.2fs (batch_size=%d)",
                        rows_loaded,
                        time.perf_counter() - load_start,
                        settings.COPY_BATCH_SIZE,
                    )

                else:
                    # ── FALLBACK PATH ──────────────────────────────────────
                    # Write / reuse a clean intermediate file, then COPY.
                    # Useful when the clean file is already cached from a
                    # previous run and SINGLE_PASS_LOAD is False.
                    t_clean = time.perf_counter()
                    if clean_file_cached:
                        logging.info("Clean file cached, skipping cleaning: %s", clean_path)
                    else:
                        logging.info("Clean file not found → cleaning")
                        clean_dat(dat_path, clean_path)
                    logging.info("Clean step: %.2fs", time.perf_counter() - t_clean)

                    t_copy = time.perf_counter()
                    rows_loaded = await copy_to_staging(
                        session,
                        clean_path,
                        file_date_obj,
                        batch_size=settings.COPY_BATCH_SIZE,
                        max_rows=max_rows,
                    )
                    logging.info(
                        "Copy-from-file load done: %d rows in %.2fs (batch_size=%d)",
                        rows_loaded,
                        time.perf_counter() - t_copy,
                        settings.COPY_BATCH_SIZE,
                    )

                # ──────────────────── POST-LOAD ──────────────────── #
                if settings.ENABLE_POST_LOAD_COUNT:
                    row_count = await get_staging_count(session, file_date_obj)
                    logging.info(
                        "Verified %d rows in staging for %s", row_count, resolved_file_date
                    )

                logging.info(
                    "Pipeline completed in %.2fs",
                    time.perf_counter() - pipeline_start,
                )

            except Exception as exc:
                logging.exception("Pipeline failed for %s: %s", file_date, exc)
                raise


async def run_pipeline(file_date: str) -> None:
    await run_pipeline_async(file_date)


if __name__ == "__main__":
    today = datetime.now()
    file_date = today.strftime("%Y%m01")
    asyncio.run(run_pipeline(file_date))
