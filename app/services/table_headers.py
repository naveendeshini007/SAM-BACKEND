from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.table_headers import TableHeaders
from app.schemas.table_headers import ColumnHeader


class TableService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_visible_columns(self, table_name: str) -> list[ColumnHeader]:
        result = await self._db.execute(
            select(TableHeaders)
            .where(TableHeaders.table_name == table_name)
            .where(TableHeaders.is_visible.is_(True))
            .order_by(TableHeaders.order)
        )
        rows = result.scalars().all()
        return [ColumnHeader.model_validate(row) for row in rows]