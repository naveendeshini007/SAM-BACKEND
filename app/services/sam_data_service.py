from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from math import ceil
from app.schemas.sam_data import SamDataListSchema, SamDataDetailSchema

from app.models.sam_data import SamData

class SamDataService:
#GET ORGANIZATIONS
    @staticmethod
    async def get_organizations(
        db: AsyncSession,
        page: int = 1,
        limit: int = 10,
        search: str = None,
        state: str = None,
        year: int = None,
        month: int = None
    ):
        try:
            # Input validation
            if page < 1:
                raise HTTPException(status_code=400, detail="Page must be >= 1")

            if limit < 1 or limit > 100:
                raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

            query = select(SamData)

            # Search
            if search:
                query = query.where(
                    or_(
                        SamData.organization_name.ilike(f"%{search}%"),
                        SamData.city.ilike(f"%{search}%"),
                        SamData.state.ilike(f"%{search}%")
                    )
                )

            # Filter (state)
            if state:
                query = query.where(SamData.state == state)

            # Year filter
            if year:
                query = query.where(
                    SamData.registration_date.startswith(str(year))
                )

            # Month filter
            if month:
                query = query.where(
                    SamData.registration_date[4:6] == f"{month:02d}"
                )

            #  Efficient total count (NO full data load)
            count_query = query.with_only_columns(func.count()).order_by(None)
            total = (await db.execute(count_query)).scalar()

            #  Pagination
            skip = (page - 1) * limit
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            rows = result.scalars().all()

            data = [SamDataListSchema.model_validate(row) for row in rows]

            # Total pages
            total_pages = ceil(total / limit) if limit else 1

            return {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "data": data
            }

        except HTTPException:
            raise

        except SQLAlchemyError as exception:
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(exception)}"
            )

        except Exception as exception:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(exception)}"
            )
# GET SINGLE ORGANIZATION
    @staticmethod
    async def get_organization_by_id(
        db: AsyncSession,
        record_id: str
    ):
        try:
            query = select(SamData).where(SamData.record_id == record_id)
            result = await db.execute(query)

            organization = result.scalar_one_or_none()

            if not organization:
                raise HTTPException(
                    status_code=404,
                    detail="Organization not found"
                )

            return SamDataDetailSchema.model_validate(organization)

        except HTTPException:
            raise

        except SQLAlchemyError as exception:
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(exception)}"
            )

        except Exception as exception:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(exception)}"
            )
# SEARCH AND FILTER ORGANIZATIONS
    @staticmethod
    async def search_organizations(
        db: AsyncSession,
        page: int = 1,
        limit: int = 10,
        search : str = None,
        state: str = None,
        year: str = None,
        month: str = None
    ):
        try:
            if page < 1:
                raise HTTPException(status_code=400, detail="Page must be >= 1")
            if limit < 1 or limit > 100:
                raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

            query = select(SamData)

            if search:
                query = query.where(
                    or_(
                        SamData.organization_name.ilike(f"%{search}%"),
                        SamData.city.ilike(f"%{search}%"),
                        SamData.state.ilike(f"%{search}%")
                    )
                )
            if state:
                query = query.where(
                    SamData.state == state)
            if year:
                query = query.where(
                    SamData.registration_date.startswith(str(year))
                )
            if month:
                query = query.where(SamData.registration_date[4:6] == f"{month:02d}")
            
            count_query = query.with_only_columns(func.count()).order_by(None)
            total = (await db.execute(count_query)).scalar()

            skip = (page - 1) * limit
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            rows = result.scalars().all()

            data = [SamDataListSchema.model_validate(row) for row in rows ]

            total_pages = ceil(total/ limit) if limit else 1

            return {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages":total_pages,
                "data": data
            }
        
        except HTTPException as exception:
            raise
        except SQLAlchemyError as exception:
            raise HTTPException(status_code=500, detail=f"Database error: {str(exception)}")
        except Exception as exception:
            raise HTTPException(status_code=500, detail=f"Unexpected error:{str(exception)}")