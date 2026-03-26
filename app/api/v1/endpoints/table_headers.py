# app/routers/table_headers.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.table_headers import TableHeadersService
from app.schemas.table_headers import (
    FrontendColumnsResponse,
    TableHeadersCreateSchema,
    TableHeadersResponse,
    TableHeadersUpdateSchema,
)

router = APIRouter()


# ── Frontend consumer ─────────────────────────────────────────────────────────

@router.get(
    "/{table_name}",
    response_model=FrontendColumnsResponse,
    summary="Get visible columns for a table (used by frontend)",
)
async def get_visible_columns(
    table_name: str,
    db: AsyncSession = Depends(get_db),
):
    return await TableHeadersService.get_visible_columns(db, table_name)


# ── Admin: full config ────────────────────────────────────────────────────────

@router.get(
    "/{table_name}/config",
    response_model=TableHeadersResponse,
    summary="Get full header config for a table (admin)",
)
async def get_table_config(
    table_name: str,
    db: AsyncSession = Depends(get_db),
):
    return await TableHeadersService.get_by_table_name(db, table_name)


@router.post(
    "",
    response_model=TableHeadersResponse,
    status_code=201,
    summary="Create header config for a new table (admin)",
)
async def create_table_headers(
    payload: TableHeadersCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    return await TableHeadersService.create(db, payload)


@router.patch(
    "/{table_name}",
    response_model=TableHeadersResponse,
    summary="Update columns or toggle active status (admin)",
)
async def update_table_headers(
    table_name: str,
    payload: TableHeadersUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    return await TableHeadersService.update(db, table_name, payload)