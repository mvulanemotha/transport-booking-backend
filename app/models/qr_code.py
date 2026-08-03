from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, func, Text, Boolean, JSON, Integer
from sqlalchemy.orm import relationship
import uuid

from app.core.database import BaseModel


class QRCode(BaseModel):
    """QR Code model for ticket verification and check-in"""
    __tablename__ = "qr_codes"

    # Booking reference
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False, index=True)

    # QR Code data
    code = Column(String(100), unique=True, nullable=False, index=True)
    data = Column(JSON, nullable=False)  # Encoded booking data

    # Validity
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_valid = Column(Boolean, default=True, index=True)

    # Scan tracking
    scanned_at = Column(DateTime(timezone=True), nullable=True)
    scanned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    scan_count = Column(Integer, default=0)
    last_scan_ip = Column(String(50), nullable=True)
    scan_location = Column(JSON, nullable=True)  # {lat, lng, address}

    # Security
    device_info = Column(JSON, nullable=True)  # Device info from scan
    verification_attempts = Column(Integer, default=0)
    is_blocked = Column(Boolean, default=False)
    blocked_at = Column(DateTime(timezone=True), nullable=True)
    block_reason = Column(String(255), nullable=True)

    # Relationships
    booking = relationship("Booking", backref="qr_codes")
    scanner = relationship("User", foreign_keys=[scanned_by])

    def __repr__(self):
        return f"<QRCode {self.code} for booking {self.booking_id}>"