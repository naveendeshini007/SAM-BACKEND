from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.table_headers import TableColumnsResponse
from app.services.table_headers import TableService

router = APIRouter()


@router.get(
    "/{table_name}",
    response_model=TableColumnsResponse,
    summary="Get visible column headers for a table",
)
async def get_table_headers(
    table_name: str,
    db: AsyncSession = Depends(get_db),
) -> TableColumnsResponse:
    service = TableService(db)
    columns = await service.get_visible_columns(table_name)

    if not columns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No visible columns found for table '{table_name}'.",
        )

    return TableColumnsResponse(table_name=table_name, columns=columns)