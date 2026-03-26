# app/schemas/table_headers.py
from pydantic import BaseModel, Field
from typing import Optional
import uuid


# ─── Individual column definition (lives inside columns_schema JSON) ──────────

class ColumnDefinition(BaseModel):
    column_name:  str
    display_name: str
    order:        int
    is_visible:   bool = True


# ─── Request body for creating / replacing a table's header config ────────────

class TableHeadersCreateSchema(BaseModel):
    table_name:     str = Field(..., max_length=100)
    columns_schema: list[ColumnDefinition]


# ─── Request body for partial update (PATCH) ─────────────────────────────────

class TableHeadersUpdateSchema(BaseModel):
    columns_schema: Optional[list[ColumnDefinition]] = None
    is_active:      Optional[bool] = None


# ─── Full response (used for admin / management endpoints) ────────────────────

class TableHeadersResponse(BaseModel):
    table_header_id: uuid.UUID
    table_name:      str
    columns_schema:  list[ColumnDefinition]
    is_active:       bool

    model_config = {"from_attributes": True}


# ─── Slim response consumed by the frontend to render table columns ───────────
# Only visible columns, sorted by order.

class FrontendColumnsResponse(BaseModel):
    table_name: str
    columns:    list[ColumnDefinition]   # is_visible=True, sorted by order