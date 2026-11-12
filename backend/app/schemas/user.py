"""
Pydantic Schemas for Users and Merchant Profiles.
"""

from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    phone_number: str
    full_name: str
    email: EmailStr | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone_number: str
    full_name: str
    email: str | None = None
    is_active: bool = True
    created_at: datetime
