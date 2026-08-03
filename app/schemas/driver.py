from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class DriverBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=10, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    license_number: str = Field(..., min_length=2, max_length=100)
    license_class: str = Field(..., min_length=1, max_length=50)
    license_expiry: date
    license_issued: Optional[date] = None
    medical_expiry: Optional[date] = None
    passport_number: Optional[str] = None
    passport_expiry: Optional[date] = None
    id_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    status: Optional[str] = "active"
    notes: Optional[str] = None


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    license_number: Optional[str] = Field(None, min_length=2, max_length=100)
    license_class: Optional[str] = Field(None, min_length=1, max_length=50)
    license_expiry: Optional[date] = None
    license_issued: Optional[date] = None
    medical_expiry: Optional[date] = None
    passport_number: Optional[str] = None
    passport_expiry: Optional[date] = None
    id_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    is_available: Optional[bool] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class DriverResponse(DriverBase):
    id: str
    user_id: Optional[str] = None
    is_available: bool
    status: str
    trips_completed: int = 0
    rating: Decimal = Decimal('5.0')
    total_earnings: Decimal = Decimal('0')
    hire_date: Optional[date] = None
    contract_end: Optional[date] = None
    languages: Optional[str] = None
    specialties: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DriverListResponse(BaseModel):
    items: list[DriverResponse]
    total: int
    page: int
    page_size: int
    total_pages: int