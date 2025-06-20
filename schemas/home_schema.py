from pydantic import BaseModel
from typing import Optional
from fastapi import UploadFile

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