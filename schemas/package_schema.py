# schemas/package_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class PackageType(str, Enum):
    USER = "user"
    APP = "app"

class PackageBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    stripe_price_id: str
    type: PackageType = PackageType.USER
    is_active: bool = True

class PackageCreate(PackageBase):
    pass

class PackageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    stripe_price_id: Optional[str] = None
    type: Optional[PackageType] = None
    is_active: Optional[bool] = None

class PackageInDB(PackageBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime