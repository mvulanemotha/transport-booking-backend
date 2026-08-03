from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time, datetime
from decimal import Decimal


class ScheduleBase(BaseModel):
    route_id: str
    departure_location: str = Field(..., min_length=2, max_length=255)
    destination: str = Field(..., min_length=2, max_length=255)
    departure_location_detail: Optional[str] = None
    destination_detail: Optional[str] = None
    departure_date: date
    departure_time: time
    estimated_arrival: Optional[time] = None
    vehicle_id: str
    driver_id: str
    price: Decimal = Field(..., ge=0)
    notes: Optional[str] = None


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    departure_location: Optional[str] = Field(None, min_length=2, max_length=255)
    destination: Optional[str] = Field(None, min_length=2, max_length=255)
    departure_location_detail: Optional[str] = None
    destination_detail: Optional[str] = None
    departure_date: Optional[date] = None
    departure_time: Optional[time] = None
    estimated_arrival: Optional[time] = None
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class ScheduleResponse(ScheduleBase):
    id: str
    code: str
    capacity: int
    booked_seats: int
    available_seats: int
    dynamic_price: Optional[Decimal] = None
    surge_multiplier: Decimal = Decimal('1.0')
    status: str
    is_holiday: bool = False
    is_peak: bool = False
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleListResponse(BaseModel):
    items: list[ScheduleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int