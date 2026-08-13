from pydantic import BaseModel, Field , UUID4
from typing import Optional
from datetime import datetime
from decimal import Decimal


class RouteBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=255)
    origin: str = Field(..., min_length=2, max_length=255)
    destination: str = Field(..., min_length=2, max_length=255)
    origin_lat: Optional[Decimal] = None
    origin_lng: Optional[Decimal] = None
    dest_lat: Optional[Decimal] = None
    dest_lng: Optional[Decimal] = None
    distance_km: Optional[Decimal] = None
    estimated_duration: Optional[str] = None
    base_price: Decimal = Field(..., ge=0)
    is_international: bool = False
    border_crossing: Optional[str] = None
    waypoints: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None


class RouteCreate(RouteBase):
    pass


class RouteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    origin: Optional[str] = Field(None, min_length=2, max_length=255)
    destination: Optional[str] = Field(None, min_length=2, max_length=255)
    origin_lat: Optional[Decimal] = None
    origin_lng: Optional[Decimal] = None
    dest_lat: Optional[Decimal] = None
    dest_lng: Optional[Decimal] = None
    distance_km: Optional[Decimal] = None
    estimated_duration: Optional[str] = None
    base_price: Optional[Decimal] = Field(None, ge=0)
    is_international: Optional[bool] = None
    border_crossing: Optional[str] = None
    waypoints: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class RouteResponse(RouteBase):
    id: UUID4  # ✅ Accept UUID, will be serialized to string
    created_by: UUID4  # ✅ Accept UUID, will be serialized to string
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RouteListResponse(BaseModel):
    items: list[RouteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int