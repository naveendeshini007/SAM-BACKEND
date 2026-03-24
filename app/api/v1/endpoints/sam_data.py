from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

# correct import path
from app.services.sam_data_service import (
    get_sam_data,
    filter_sam_data,
    search_sam_data)

router = APIRouter()


# GET API
@router.get("/")
async def fetch_sam_data(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    return await get_sam_data(db, skip, limit)


# FILTER API
@router.get("/filter")
async def filter_data(
    skip: int = 0,
    limit: int = 50,
    C1: str = None,
    C2: str = None,
    C3: str = None,
    file_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    filters = {
        "C1": C1,
        "C2": C2,
        "C3": C3,
        "file_id": file_id
    }

    return await filter_sam_data(db, filters, skip, limit)
#Search API

@router.get("/search")
async def search_data(
    query: str,
    skip: int = 0,
    limit: int = 50,
    db = Depends(get_db)
):
    return await search_sam_data(db, query, skip, limit)