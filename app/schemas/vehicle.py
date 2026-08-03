from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class VehicleBase(BaseModel):
    registration: str = Field(..., min_length=2, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    vehicle_type: str
    capacity: int = Field(..., ge=1)
    color: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    insurance_expiry: Optional[date] = None
    license_number: Optional[str] = None
    license_expiry: Optional[date] = None
    roadworthy_certificate: Optional[str] = None
    roadworthy_expiry: Optional[date] = None
    status: Optional[str] = "available"
    fuel_type: Optional[str] = None
    fuel_efficiency: Optional[Decimal] = None
    tracking_device_id: Optional[str] = None
    gps_enabled: bool = False
    notes: Optional[str] = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    vehicle_type: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=1)
    color: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    insurance_expiry: Optional[date] = None
    license_number: Optional[str] = None
    license_expiry: Optional[date] = None
    roadworthy_certificate: Optional[str] = None
    roadworthy_expiry: Optional[date] = None
    status: Optional[str] = None
    fuel_type: Optional[str] = None
    fuel_efficiency: Optional[Decimal] = None
    tracking_device_id: Optional[str] = None
    gps_enabled: Optional[bool] = None
    notes: Optional[str] = None


class VehicleResponse(VehicleBase):
    id: str
    status: str
    last_maintenance: Optional[date] = None
    next_maintenance: Optional[date] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VehicleListResponse(BaseModel):
    items: list[VehicleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int