# schemas/app_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class AppBase(BaseModel):
    owner_id: str
    name: str = Field(..., min_length=2, max_length=100)
    description: str
    is_active: bool = True

class AppCreate(AppBase):
    pass

class AppUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class AppInDB(AppBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime