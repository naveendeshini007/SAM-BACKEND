from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Query
from app.services.pipeline import run_pipeline_service

router = APIRouter()


def _first_sunday_file_date(year: int, month: int) -> str:
    first_day = date(year, month, 1)
    # Python weekday: Monday=0 ... Sunday=6
    days_until_sunday = (6 - first_day.weekday()) % 7
    first_sunday = first_day + timedelta(days=days_until_sunday)
    return first_sunday.strftime("%Y%m%d")


@router.post("/")
def run_pipeline(
    background_tasks: BackgroundTasks,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    force_reload: bool = False,
):
    """
    Trigger pipeline asynchronously using year/month.
    Internally computes the first Sunday and passes it as file_date (YYYYMMDD).
    """
    file_date = _first_sunday_file_date(year, month)

    # BackgroundTasks can execute async callables; this keeps one event loop model.
    background_tasks.add_task(run_pipeline_service, file_date, force_reload)

    return {
        "status": "Pipeline started",
        "year": year,
        "month": month,
        "file_date": file_date,
        "force_reload": force_reload,
    }
    