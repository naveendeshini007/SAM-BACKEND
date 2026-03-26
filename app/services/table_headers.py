# app/services/table_headers_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from app.models.table_headers import TableHeaders
from app.schemas.table_headers import (
    ColumnDefinition,
    FrontendColumnsResponse,
    TableHeadersCreateSchema,
    TableHeadersResponse,
    TableHeadersUpdateSchema,
)


class TableHeadersService:

    # ── Frontend consumer ─────────────────────────────────────────────────────

    @staticmethod
    async def get_visible_columns(
        db: AsyncSession,
        table_name: str,
    ) -> FrontendColumnsResponse:
        """
        Returns only is_visible=True columns, sorted by order.
        Called by the frontend to build table headers dynamically.
        """
        try:
            row = await TableHeadersService._get_active_row(db, table_name)

            visible = sorted(
                [col for col in row.columns_schema if col.get("is_visible", True)],
                key=lambda c: c.get("order", 0),
            )

            columns = [ColumnDefinition(**col) for col in visible]
            return FrontendColumnsResponse(table_name=table_name, columns=columns)

        except HTTPException:
            raise
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    # ── Admin: get full config ────────────────────────────────────────────────

    @staticmethod
    async def get_by_table_name(
        db: AsyncSession,
        table_name: str,
    ) -> TableHeadersResponse:
        try:
            row = await TableHeadersService._get_active_row(db, table_name)
            return TableHeadersResponse.model_validate(row)
        except HTTPException:
            raise
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    # ── Admin: create ─────────────────────────────────────────────────────────

    @staticmethod
    async def create(
        db: AsyncSession,
        payload: TableHeadersCreateSchema,
    ) -> TableHeadersResponse:
        try:
            existing = await db.execute(
                select(TableHeaders).where(TableHeaders.table_name == payload.table_name)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail=f"Header config for '{payload.table_name}' already exists. Use PATCH to update.",
                )

            row = TableHeaders(
                table_name=payload.table_name,
                columns_schema=[col.model_dump() for col in payload.columns_schema],
            )
            db.add(row)
            await db.commit()
            await db.refresh(row)
            return TableHeadersResponse.model_validate(row)

        except HTTPException:
            raise
        except SQLAlchemyError as exc:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    # ── Admin: partial update ─────────────────────────────────────────────────

    @staticmethod
    async def update(
        db: AsyncSession,
        table_name: str,
        payload: TableHeadersUpdateSchema,
    ) -> TableHeadersResponse:
        try:
            row = await TableHeadersService._get_active_row(db, table_name)

            if payload.columns_schema is not None:
                row.columns_schema = [col.model_dump() for col in payload.columns_schema]
            if payload.is_active is not None:
                row.is_active = payload.is_active

            await db.commit()
            await db.refresh(row)
            return TableHeadersResponse.model_validate(row)

        except HTTPException:
            raise
        except SQLAlchemyError as exc:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    # ── Internal helper ───────────────────────────────────────────────────────

    @staticmethod
    async def _get_active_row(db: AsyncSession, table_name: str) -> TableHeaders:
        result = await db.execute(
            select(TableHeaders).where(
                TableHeaders.table_name == table_name,
                TableHeaders.is_active.is_(True),
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"No active header config found for table '{table_name}'.",
            )
        return row