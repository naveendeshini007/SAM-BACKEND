from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sam_data_service import SamDataService
from app.services.sam_date import SamDateService
from app.services.pipeline import run_pipeline_service
from app.core.database import get_db
from typing import Optional
from app.schemas.pagination import PaginationParams

router = APIRouter()

#GET ORGANIZATIONS
@router.get("/organizations")
async def fetch_organizations(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await SamDataService.get_organizations(
        db=db,
        page=pagination.page,
        limit=pagination.limit
    )

# GET SINGLE ORGANIZATION
@router.get("/organizations/{record_id}")
async def fetch_organization(
    record_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await SamDataService.get_organization_by_id(db, record_id)

#GET FILTER & SEARCH API  
@router.get("/organizations/search")
async def search_organizations(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = None,
    state: Optional[str] = None,
    year: Optional[str] = None,
    month: Optional[str] = None,
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
 