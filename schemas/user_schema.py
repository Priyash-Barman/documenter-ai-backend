# schemas/user_schema.py
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from defaults.enums import UserRole

class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: UserRole = UserRole.END_USER

class UserCreate(UserBase):
    full_name: str = Field(None, min_length=2, max_length=100)
    email: EmailStr = None
    role: Optional[UserRole] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None

class UserStatusUpdate(BaseModel):
    is_active: bool

class UserInDB(UserBase):
    id: str = Field(..., alias="_id")
    is_active: bool
    created_at: datetime
    updated_at: datetime
