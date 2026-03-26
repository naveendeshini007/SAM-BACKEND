import os
import logging
import asyncio
from datetime import datetime
from app.services.downloader import download_file
from app.services.extractor import extract_zip, clean_dat
from sqlalchemy import text

from app.db.session import (
    AsyncSessionLocal,
    copy_to_staging,
    delete_staging_for_date,
    delete_entities_for_date,
    get_staging_count,
    init_db,
    upsert,
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


async def run_pipeline_async(file_date: str, force_reload: bool = False) -> None:
    async with _pipeline_lock:
        async with AsyncSessionLocal() as session:
            await init_db(session)

            try:
                # `sam_entities.file_date` is a DATE column, but `file_date` we receive is
                # a string like "YYYYMM01". Convert it to a real `datetime.date` for asyncpg.
                file_date_obj = datetime.strptime(file_date, "%Y%m%d").date()

                max_rows = settings.LIMIT_ROWS
                if max_rows is None:
                    logging.info("Active LIMIT_ROWS: ALL (no row limit)")
                else:
                    logging.info(f"Active LIMIT_ROWS: {max_rows}")

                if force_reload:
                    deleted_rows = await delete_entities_for_date(session, file_date_obj)
                    logging.info(
                        f"force_reload enabled for {file_date}; "
                        f"deleted {deleted_rows} existing rows"
                    )

                logging.info(f"Starting pipeline for {file_date}")

                zip_name = f"SAM_{file_date}.zip"
                zip_path = os.path.join(settings.DOWNLOAD_FOLDER, zip_name)

                dat_name = f"SAM_PUBLIC_UTF-8_MONTHLY_V2_{file_date}.dat"
                dat_path = os.path.join(settings.DOWNLOAD_FOLDER, dat_name)

                clean_path = os.path.join(
                    settings.DOWNLOAD_FOLDER,
                    f"clean_{file_date}.dat",
                )

                # ---------------- DOWNLOAD ---------------- #
                if os.path.exists(zip_path):
                    logging.info(f"ZIP exists, skipping download: {zip_path}")
                else:
                    logging.info("ZIP not found -> downloading")
                    zip_path = download_file(file_date)

                # ---------------- EXTRACT ---------------- #
                if os.path.exists(dat_path):
                    logging.info(f"DAT exists, skipping extraction: {dat_path}")
                else:
                    logging.info("DAT not found -> extracting")
                    dat_file = extract_zip(zip_path)
                    dat_path = os.path.join(settings.DOWNLOAD_FOLDER, dat_file)

                # ---------------- CLEAN ---------------- #
                if os.path.exists(clean_path):
                    logging.info(f"CLEAN file exists, skipping cleaning: {clean_path}")
                else:
                    logging.info("CLEAN file not found -> cleaning")
                    clean_dat(dat_path, clean_path)

                # ---------------- LOAD ---------------- #
                logging.info("Loading into staging")
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
                    max_rows=max_rows,
                )

                row_count = await get_staging_count(session, file_date_obj)
                logging.info(f"Rows in staging for {file_date}: {row_count}")

                res = await session.execute(
                    text(
                        """
                        SELECT COUNT(DISTINCT col1)
                        FROM sam_staging_raw
                        WHERE file_date = :file_date
                        """
                    ),
                    {"file_date": file_date_obj},
                )
                unique_count = int(res.scalar_one())
                logging.info(f"Unique UEI count (after dedup): {unique_count}")

                logging.info("Upserting into final table")
                await upsert(session, file_date_obj)

                logging.info("Pipeline completed successfully")

            except Exception as e:
                logging.exception(f"Pipeline failed for {file_date}: {e}")
                raise


async def run_pipeline(file_date: str, force_reload: bool = False) -> None:
    # Keep execution on FastAPI's running event loop.
    await run_pipeline_async(file_date, force_reload=force_reload)


if __name__ == "__main__":
    today = datetime.now()
    file_date = today.strftime("%Y%m01")

    asyncio.run(run_pipeline(file_date))