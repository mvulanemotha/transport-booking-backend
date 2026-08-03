from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class QRCodeBase(BaseModel):
    """Base QR Code schema"""
    booking_id: str
    expires_at: datetime


class QRCodeCreate(QRCodeBase):
    """Schema for creating a QR code"""
    pass


class QRCodeResponse(BaseModel):
    """QR Code response schema"""
    id: str
    booking_id: str
    code: str
    data: Dict[str, Any]
    expires_at: datetime
    is_valid: bool
    scan_count: int
    is_blocked: bool
    blocked_at: Optional[datetime] = None
    block_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QRCodeGenerateResponse(BaseModel):
    """Response when generating a QR code"""
    qr_code: str  # The QR code string
    qr_data: Dict[str, Any]
    expires_at: datetime
    qr_image: Optional[str] = None  # Base64 encoded image


class QRCodeValidateRequest(BaseModel):
    """Request to validate a QR code"""
    qr_code: str
    scan_location: Optional[Dict[str, Any]] = None
    device_info: Optional[Dict[str, Any]] = None


class QRCodeValidateResponse(BaseModel):
    """Response when validating a QR code"""
    valid: bool
    message: str
    booking_id: Optional[str] = None
    reference: Optional[str] = None
    passenger_name: Optional[str] = None
    status: Optional[str] = None
    schedule: Optional[Dict[str, Any]] = None