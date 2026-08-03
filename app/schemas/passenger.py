from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime


class PassengerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=50)
    email: Optional[EmailStr] = None
    id_number: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    seat_number: Optional[str] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    special_requests: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    luggage_count: int = 0
    luggage_weight: Optional[int] = None


class PassengerCreate(PassengerBase):
    pass


class PassengerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=50)
    email: Optional[EmailStr] = None
    seat_number: Optional[str] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    special_requests: Optional[str] = None
    is_checked_in: Optional[bool] = None
    is_boarded: Optional[bool] = None


class PassengerResponse(PassengerBase):
    id: str
    booking_id: str
    is_checked_in: bool
    checked_in_at: Optional[datetime] = None
    is_boarded: bool
    boarded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True