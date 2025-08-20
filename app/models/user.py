from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.VIEWER
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True