from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sam_data_service import SamDataService
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