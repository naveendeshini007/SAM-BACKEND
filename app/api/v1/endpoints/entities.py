import logging

from fastapi import APIRouter, Depends, HTTPException, status
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
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to fetch entities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch entities",
        ) from e