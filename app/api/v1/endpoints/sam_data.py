from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sam_data_service import SamDataService
from app.core.database import get_db
from typing import Optional

router = APIRouter()


#GET ORGANIZATIONS
@router.get("/organizations")
async def fetch_organizations(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    search: Optional[str] = None,
    state: Optional[str] = (None),
    year: Optional[int] = (None),
    month: Optional[int] = (None),
    db: AsyncSession = Depends(get_db),
):
    return await SamDataService.get_organizations(
        db=db,
        page=page,
        limit=limit,
        search=search,
        state=state,
        year=year,
        month=month
    )

# GET SINGLE ORGANIZATION
@router.get("/organizations/{record_id}")
async def fetch_organization(
    record_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await SamDataService.get_organization_by_id(db, record_id)