# schemas/history_schema.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional

class RequestFrom(str, Enum):
    USER = "user"
    APP = "app"

class HistoryBase(BaseModel):
    req_text: str
    req_file_url: Optional[str] = None
    res_text: str
    res_file_url: Optional[str] = None
    req_from: RequestFrom
    user_id: Optional[str] = None
    app_id: Optional[str] = None

class HistoryInDB(HistoryBase):
    id: str = Field(..., alias="_id")
    timestamp: datetime