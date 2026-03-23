from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sam_data import SamData


# GET API
async def get_sam_data(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50
):
    query = select(SamData).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# FILTER API
async def filter_sam_data(
    db: AsyncSession,
    filters: dict,
    skip: int = 0,
    limit: int = 50
):
    query = select(SamData)

    for key, value in filters.items():
        if hasattr(SamData, key) and value is not None:
            query = query.where(getattr(SamData, key) == value)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()

#SEARCH API
async def search_sam_data(
        db: AsyncSession,
        query_str: str,
        skip: int = 0,
        limit: int = 50
):
    query = select(SamData).where(
            SamData.C1.ilike(f"%{query_str}"),
            SamData.C2.ilike(f"%{query_str}%"),
            SamData.C3.ilike(f"%{query_str}%")
    )

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()