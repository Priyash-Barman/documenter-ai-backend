# schemas/profile_schema.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from defaults.enums import UserRole

class ProfileView(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    # Add more fields as needed
    # phone: Optional[str] = None
    # bio: Optional[str] = Field(None, max_length=500)

class ProfileUpdateResponse(BaseModel):
    success: bool
    message: str
    profile: Optional[ProfileView] = None