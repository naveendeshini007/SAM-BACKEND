from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.entities import get_entities
from app.api.deps import get_db

router = APIRouter()


@router.get("/")
async def fetch_entities(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    data = await get_entities(
        db,
        limit=limit,
        offset=offset,
    )

    return {
        "count": len(data),
        "limit": limit,
        "offset": offset,
        "data": data
    }
    

































# from fastapi import APIRouter
# from app.services.entities import get_entities

# router = APIRouter(prefix="/entities")


# @router.get("/")
# def fetch_entities(limit: int = 10):
#     data = get_entities(limit)
#     return {
#         "count": len(data),
#         "data": data
#     }