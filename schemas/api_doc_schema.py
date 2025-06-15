# schemas/api_doc_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class ApiDocBase(BaseModel):
    url: str
    method: HttpMethod
    payload: str
    response: str
    authentication: str
    description: str
    demo_url: str
    created_by: str
    is_active: bool = True

class ApiDocCreate(ApiDocBase):
    pass

class ApiDocUpdate(BaseModel):
    url: Optional[str] = None
    method: Optional[HttpMethod] = None
    payload: Optional[str] = None
    response: Optional[str] = None
    authentication: Optional[str] = None
    description: Optional[str] = None
    demo_url: Optional[str] = None
    is_active: Optional[bool] = None

class ApiDocInDB(ApiDocBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime