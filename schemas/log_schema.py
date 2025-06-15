# schemas/log_schema.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Dict, Any

class LogType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"

class LogBase(BaseModel):
    type: LogType
    created_by: str
    details: Dict[str, Any]

class LogInDB(LogBase):
    id: str = Field(..., alias="_id")
    created_at: datetime