from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.services.sam_download import SamDownloadService
from app.services.sam_data_service import SamDataService
from app.services.sam_date import SamDateService
from app.services.pipeline import run_pipeline_service
from app.core.database import get_db
from typing import Optional
from app.schemas.pagination import PaginationParams
from app.schemas.sam_data import SamDataListSchema, SamDataDetailSchema
from app.schemas.pagination import PaginationParams, PaginatedResponse

router = APIRouter()


# ── Search + filter + paginate (must be registered BEFORE /{record_id}) ───────
@router.get(
    "/search",
    response_model=PaginatedResponse[SamDataListSchema],
    summary="Search and filter organizations with pagination",
)
async def search_organizations(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search by name, city, or state"),
    state: Optional[str] = Query(None, description="Filter by state code (e.g. CA)"),
    year: Optional[str] = Query(None, description="Filter by registration year (e.g. 2023)"),
    month: Optional[str] = Query(None, description="Filter by registration month (e.g. 01)"),
    db: AsyncSession = Depends(get_db),
):
    return await SamDataService.search_organizations(
        db=db,
        page=pagination.page,
        limit=pagination.limit,
        search=search,
        state=state,
        year=year,
        month=month
    )

# ── List all (no filters) ──────────────────────────────────────────────────────
@router.get(
    "",
    response_model=PaginatedResponse[SamDataListSchema],
    summary="List all organizations with pagination",
)
async def list_organizations(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await SamDataService.search_organizations(
        db=db,
        page=pagination.page,
        limit=pagination.limit,
    )

# ── Pipeline trigger (must come BEFORE /{record_id}) ─────────────────────────
@router.get(
    "/download",
    summary="Run full SAM pipeline (download, clean, load)"
)
async def download_sam_data(
    background_tasks: BackgroundTasks,
    year: int,
    month: int,
):
    """
    Trigger full pipeline for given year/month.
    """
    try:
        if month < 1 or month > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Month must be between 1 and 12"
            )

        file_date = SamDateService.get_first_sunday(year, month)
        background_tasks.add_task(run_pipeline_service, file_date)

        return {
            "status": "Pipeline started",
            "year": year,
            "month": month,
            "file_date": file_date,
            "flow": "download -> extract -> clean -> load",
        }

    except HTTPException:
        raise

    except Exception as exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exception)
        )

# ── Single organization (must come AFTER all literal paths) ───────────────────
@router.get(
    "/{record_id}",
    response_model=SamDataDetailSchema,
    summary="Get a single organization by record_id",
)
async def get_organization(
    record_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await SamDataService.get_organization_by_id(db, record_id)

