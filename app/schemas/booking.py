from pydantic import BaseModel, Field ,UUID4
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from app.schemas.passenger import PassengerCreate, PassengerResponse


class BookingBase(BaseModel):
    schedule_id: str
    customer_id: Optional[str] = None   # ← make optional
    number_of_passengers: int = Field(1, ge=1, le=20)
    source: Optional[str] = "website"
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    notes: Optional[str] = None

class BookingCreate(BookingBase):
    passengers: List[PassengerCreate]


class BookingUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None


class BookingResponse(BookingBase):
    id: UUID4
    reference: str
    vehicle_id: UUID4
    route_id: UUID4
    schedule_id: UUID4
    customer_id: UUID4
    booking_date: datetime
    number_of_seats: int
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_balance: Decimal
    status: str
    passengers: List[PassengerResponse] = []
    created_by: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# ✅ Add this missing class
class BookingFilters(BaseModel):
    status: Optional[str] = None
    source: Optional[str] = None
    customer_id: Optional[str] = None
    schedule_id: Optional[str] = None
    route_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20