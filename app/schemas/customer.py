from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class CustomerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=10, max_length=50)
    email: Optional[EmailStr] = None
    id_number: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    membership_plan: Optional[str] = "basic"
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=50)
    email: Optional[EmailStr] = None
    id_number: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    membership_plan: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: UUID4
    user_id: Optional[UUID4] = None
    membership_start: Optional[date] = None
    membership_expiry: Optional[date] = None
    loyalty_points: int = 0
    total_trips: int = 0
    total_spent: Decimal = Decimal('0')
    average_rating: Optional[Decimal] = None
    is_active: bool
    is_verified: bool
    created_by: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int