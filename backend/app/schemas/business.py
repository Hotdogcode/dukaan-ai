"""
Pydantic Schemas for Multi-Tenant Businesses and Membership.
"""

from datetime import datetime
from typing import Literal
import uuid
from pydantic import BaseModel, ConfigDict, Field


class BusinessCreate(BaseModel):
    """Payload to register a new store business."""
    name: str = Field(min_length=2, max_length=150, description="Store display name")
    business_type: str | None = Field(default="GROCERY", max_length=50, description="Business type e.g. GROCERY, RETAIL")
    owner_name: str | None = Field(default=None, max_length=120, description="Owner name")
    legal_name: str | None = Field(default=None, max_length=200)
    gstin: str | None = Field(default=None, max_length=15)
    currency: str = Field(default="INR", max_length=3)
    timezone: str = Field(default="Asia/Kolkata", max_length=50)
    primary_language: str = Field(default="hi", max_length=10)
    preferred_language: str | None = Field(default=None, max_length=10, description="Alias for primary_language")
    initial_store_name: str | None = Field(default=None, description="Name for primary store")


class BusinessUpdate(BaseModel):
    """Payload to update an existing business."""
    name: str | None = Field(default=None, min_length=2, max_length=150)
    business_type: str | None = Field(default=None, max_length=50)
    owner_name: str | None = Field(default=None, max_length=120)
    legal_name: str | None = Field(default=None, max_length=200)
    gstin: str | None = Field(default=None, max_length=15)
    primary_language: str | None = Field(default=None, max_length=10)
    timezone: str | None = Field(default=None, max_length=50)


class BusinessResponse(BaseModel):
    """Business entity details."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    business_type: str | None = None
    owner_name: str | None = None
    legal_name: str | None = None
    gstin: str | None = None
    currency: str
    timezone: str
    primary_language: str
    is_active: bool
    created_at: datetime


class StoreCreate(BaseModel):
    """Payload to create a new physical store outlet."""
    name: str = Field(min_length=2, max_length=120, description="Store display name")
    code: str | None = Field(default=None, max_length=30)
    address_line1: str = Field(default="", max_length=255, description="Street address")
    address_line2: str | None = Field(default=None, max_length=255)
    city: str = Field(default="", max_length=60)
    state: str = Field(default="", max_length=60)
    pincode: str = Field(default="", max_length=10)
    phone_number: str | None = Field(default=None, max_length=15)
    is_primary: bool = Field(default=False, description="Set as primary outlet")
    timezone: str = Field(default="Asia/Kolkata", max_length=50)


class StoreUpdate(BaseModel):
    """Payload to update an existing physical store."""
    name: str | None = Field(default=None, min_length=2, max_length=120)
    code: str | None = Field(default=None, max_length=30)
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=60)
    state: str | None = Field(default=None, max_length=60)
    pincode: str | None = Field(default=None, max_length=10)
    phone_number: str | None = Field(default=None, max_length=15)
    is_primary: bool | None = Field(default=None)
    timezone: str | None = Field(default=None, max_length=50)
    is_active: bool | None = Field(default=None)


class StoreResponse(BaseModel):
    """Store entity details."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    name: str
    code: str | None = None
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    pincode: str
    phone_number: str | None = None
    is_primary: bool
    timezone: str
    is_active: bool
    created_at: datetime


class BusinessMembershipResponse(BaseModel):
    """Business record with caller's role and granted permissions."""
    model_config = ConfigDict(from_attributes=True)

    business: BusinessResponse
    role: str
    is_active: bool
    permissions: list[str]


class MemberAddRequest(BaseModel):
    """Payload to add a new user to a business."""
    phone_number: str
    full_name: str
    role: Literal["MANAGER", "CASHIER", "INVENTORY_STAFF"] = "CASHIER"


class MemberResponse(BaseModel):
    """Business staff member response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    phone_number: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
