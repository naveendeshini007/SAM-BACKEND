from pydantic import BaseModel


class ColumnHeader(BaseModel):
    column_name:  str
    display_name: str
    order:        int

    model_config = {"from_attributes": True}


class TableColumnsResponse(BaseModel):
    table_name: str
    columns:    list[ColumnHeader]