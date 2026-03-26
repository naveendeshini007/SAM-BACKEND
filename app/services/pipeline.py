import logging
from app.services.pipeline_runner import run_pipeline  # we’ll create this next


async def run_pipeline_service(file_date: str, force_reload: bool = False):
    try:
        logging.info(
            f"API triggered pipeline for {file_date} "
            f"(force_reload={force_reload})"
        )
        await run_pipeline(file_date, force_reload=force_reload)
    except Exception as e:
        logging.exception(f"Pipeline failed: {e}")