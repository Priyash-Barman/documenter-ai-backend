from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from fastapi import UploadFile
from datetime import datetime

class ConversionRequest(BaseModel):
    model: str
    # Image will be handled separately as UploadFile

class ConversionResponse(BaseModel):
    success: bool
    message: str
    filename: str
    digitized_image: str  # base64 encoded image
    processing_time: float
    model_used: str

class ConversionHistoryItem(BaseModel):
    id: str
    filename: str
    model_used: str
    success: bool
    processing_time: float
    created_at: datetime
    completed_at: datetime
    status: str

class ConversionHistoryResponse(BaseModel):
    success: bool
    history: List[ConversionHistoryItem]
    total: int
    message: Optional[str] = None

class ConversionDetailsResponse(BaseModel):
    success: bool
    details: Optional[Dict[str, Any]] = None
    message: Optional[str] = None