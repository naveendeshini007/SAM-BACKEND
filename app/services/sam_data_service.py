# app/services/sam_data_service.py
from math import ceil

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sam_data import SamData
from app.schemas.sam_data import SamDataDetailSchema, SamDataListSchema


class SamDataService:

    @staticmethod
    async def search_organizations(
        db: AsyncSession,
        page: int = 1,
        limit: int = 10,
        search: str | None = None,
        state: str | None = None,
        year: str | None = None,
        month: str | None = None,
    ) -> dict:
        """
        Unified list + search + filter endpoint.
        All parameters are optional — omitting them returns all records paginated.
        """
        try:
            if page < 1:
                raise HTTPException(status_code=400, detail="Page must be >= 1")
            if limit < 1 or limit > 100:
                raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

            query = select(SamData)

            # Full-text search across name, city, state
            if search:
                term = f"%{search.strip()}%"
                query = query.where(
                    or_(
                        SamData.organization_name.ilike(term),
                        SamData.city.ilike(term),
                        SamData.state.ilike(term),
                        SamData.duns_number.ilike(term),
                    )
                )

            # State filter (exact match, case-insensitive)
            if state:
                query = query.where(func.upper(SamData.state) == state.upper())

            # Year filter — registration_date is stored as string (e.g. "20230115")
            if year:
                query = query.where(SamData.registration_date.startswith(year))

            # Month filter — use func.substr to avoid raw Python slicing on DB column
            if month:
                # Expects month as zero-padded string e.g. "01", "12"
                padded_month = month.zfill(2)
                query = query.where(func.substr(SamData.registration_date, 6, 2) == padded_month)

            # Efficient count without fetching rows
            count_query = select(func.count()).select_from(query.subquery())
            total: int = (await db.execute(count_query)).scalar_one()

            # Pagination
            skip = (page - 1) * limit
            query = query.order_by(SamData.organization_name).offset(skip).limit(limit)

            rows = (await db.execute(query)).scalars().all()
            data = [SamDataListSchema.model_validate(row) for row in rows]

            total_pages = ceil(total / limit) if total else 1

            return {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "data": data,
            }

        except HTTPException:
            raise
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc

    # ── Single record ─────────────────────────────────────────────────────────

    @staticmethod
    async def get_organization_by_id(db: AsyncSession, record_id: str) -> SamDataDetailSchema:
        try:
            result = await db.execute(
                select(SamData).where(SamData.record_id == record_id)
            )
            organization = result.scalar_one_or_none()

            if organization is None:
                raise HTTPException(status_code=404, detail="Organization not found")

            return SamDataDetailSchema.model_validate(organization)

        except HTTPException:
            raise
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc