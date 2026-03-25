from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sam_download import SamDownloadService
from app.services.sam_data_service import SamDataService
from app.services.sam_download import SamDownloadService
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
