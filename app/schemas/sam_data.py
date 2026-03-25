from pydantic import BaseModel
from typing import Optional


class SamDataListSchema(BaseModel):
    record_id: str
    organization_name: Optional[str]
    duns_number: Optional[str]
    status_code: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    registration_date: Optional[str]

    model_config={"from_attributes":True}


class SamDataDetailSchema(BaseModel):
    record_id: str
    duns_number: Optional[str]
    organization_name: Optional[str]
    status_code: Optional[str]
    legal_business_name: Optional[str]
    division_name: Optional[str]

    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]

    registration_date: Optional[str]
    expiration_date: Optional[str]

    website: Optional[str]

    model_config={"from_attributes":True}