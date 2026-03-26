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
    delete_staging_for_date,
    get_staging_count,
    init_db,
)
from app.core.config import settings

# logging
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/ingestion.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

_pipeline_lock = asyncio.Lock()


async def run_pipeline_async(file_date: str) -> None:
    async with _pipeline_lock:
        async with AsyncSessionLocal() as session:
            await init_db(session)

            try:
                max_rows = settings.LIMIT_ROWS
                if max_rows is None:
                    logging.info("Active LIMIT_ROWS: ALL (no row limit)")
                else:
                    logging.info(f"Active LIMIT_ROWS: {max_rows}")

                logging.info(f"Starting pipeline for {file_date}")
                pipeline_start = time.perf_counter()

                year = int(file_date[:4])
                month = int(file_date[4:6])
                download_start = time.perf_counter()
                download_service = SamDownloadService()
                download_result = download_service.download_and_extract(year, month)
                status = download_result.get("status")
                if status == "file_not_available":
                    raise RuntimeError(f"SAM source file not available for {year}-{month:02d}")
                dat_path = download_result["dat_path"]
                resolved_file_date = download_result.get("file_date", file_date)
                if resolved_file_date != file_date:
                    logging.info(
                        "Resolved file_date from sam_download differs: requested=%s resolved=%s",
                        file_date,
                        resolved_file_date,
                    )
                file_date_obj = datetime.strptime(resolved_file_date, "%Y%m%d").date()

                clean_path = os.path.join(
                    os.path.dirname(dat_path),
                    f"clean_{resolved_file_date}.dat",
                )
                logging.info("sam_download status: %s", status)
                logging.info(
                    "Download/extract step took %.2f seconds",
                    time.perf_counter() - download_start,
                )

                # ---------------- CLEAN ---------------- #
                clean_start = time.perf_counter()
                if os.path.exists(clean_path):
                    logging.info(f"CLEAN file exists, skipping cleaning: {clean_path}")
                else:
                    logging.info("CLEAN file not found -> cleaning")
                    clean_dat(dat_path, clean_path)
                logging.info(
                    "Clean step took %.2f seconds",
                    time.perf_counter() - clean_start,
                )

                # ---------------- LOAD ---------------- #
                logging.info("Loading into staging")
                load_start = time.perf_counter()
                deleted_staging = await delete_staging_for_date(session, file_date_obj)
                if deleted_staging:
                    logging.info(
                        f"Replaced staging snapshot for {file_date}; "
                        f"deleted {deleted_staging} old rows"
                    )

                await copy_to_staging(
                    session,
                    clean_path,
                    file_date_obj,
                    batch_size=settings.COPY_BATCH_SIZE,
                    max_rows=max_rows,
                )

                row_count = await get_staging_count(session, file_date_obj)
                logging.info(f"Rows in staging for {file_date}: {row_count}")
                logging.info(
                    "Load step took %.2f seconds (batch_size=%s)",
                    time.perf_counter() - load_start,
                    settings.COPY_BATCH_SIZE,
                )

                logging.info(
                    "Pipeline completed successfully in %.2f seconds",
                    time.perf_counter() - pipeline_start,
                )

            except Exception as e:
                logging.exception(f"Pipeline failed for {file_date}: {e}")
                raise


async def run_pipeline(file_date: str) -> None:
    # Keep execution on FastAPI's running event loop.
    await run_pipeline_async(file_date)


if __name__ == "__main__":
    today = datetime.now()
    file_date = today.strftime("%Y%m01")

    asyncio.run(run_pipeline(file_date))