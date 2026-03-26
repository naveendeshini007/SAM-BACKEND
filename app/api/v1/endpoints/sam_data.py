from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.services.sam_download import SamDownloadService
from app.services.sam_data_service import SamDataService
from app.schemas.sam_data import SamDataListSchema, SamDataDetailSchema
from app.schemas.pagination import PaginationParams, PaginatedResponse
from app.services.sam_export_service import SamExportService

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

# ── Single organization (must come AFTER /search) ─────────────────────────────
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

# SAM data export route
@router.get(
    "/{record_id}/export",
    summary="Export specific organization data to CSV or Excel",
)
async def export_organization(
    record_id: str,
    format: str = Query("csv", regex="^(csv|excel)$", description="File format: csv or excel"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves organization details and streams a downloadable file.
    """
    return await SamExportService.export_organization(db, record_id, format)

@router.get(
    "/download",
    summary="Download and extract SAM data"
)
async def download_sam_data(year: int, month: int):
    """
    Download SAM data for given year and month
    """
    try:
        if month < 1 or month > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Month must be between 1 and 12"
            )

        service = SamDownloadService()

        result = service.download_and_extract(year, month)
        if result["status"] == "file_not_available":
            return {
                "message": "File not available for selected month",
                "data": result
            }
        if result["status"] == "already_exists":
            return {
                "message": "File already exists",
                "data": result
            }
        if result["status"] == "extracted_existing_zip":
            return {
                "message": "ZIP extracted successfully",
                "data": result
            }
        if result["status"] == "downloaded":
            return {
                "message": "Download and extraction successful",
                "data": result
            }

        return result

    except HTTPException:
        raise

    except Exception as exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exception)
        )
 
