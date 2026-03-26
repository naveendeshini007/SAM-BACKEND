# app/routers/sam_data.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.services.sam_data_service import SamDataService
from app.schemas.sam_data import SamDataListSchema, SamDataDetailSchema
from app.schemas.pagination import PaginationParams, PaginatedResponse
from app.core.database import get_db

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
        month=month,
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