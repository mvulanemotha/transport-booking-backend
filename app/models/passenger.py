from sqlalchemy import Column, String, UUID, ForeignKey, Date, DateTime, func, Text, Boolean, Integer
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Passenger(Base):
    __tablename__ = "passengers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)

    full_name = Column(String(255), nullable=False)
    phone = Column(String(50))
    email = Column(String(255))
    id_number = Column(String(50))
    passport_number = Column(String(50))
    nationality = Column(String(100))
    date_of_birth = Column(Date)
    gender = Column(String(20))

    seat_number = Column(String(20))
    pickup_location = Column(String(255))
    dropoff_location = Column(String(255))

    special_requests = Column(Text)
    emergency_contact = Column(String(255))
    emergency_phone = Column(String(50))

    luggage_count = Column(Integer, default=0)
    luggage_weight = Column(Integer)

    is_checked_in = Column(Boolean, default=False)
    checked_in_at = Column(DateTime(timezone=True))
    checked_in_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_boarded = Column(Boolean, default=False)
    boarded_at = Column(DateTime(timezone=True))
    boarded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(DateTime(timezone=True), nullable=True)

    booking = relationship("Booking", back_populates="passengers")