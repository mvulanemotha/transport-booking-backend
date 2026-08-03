from sqlalchemy import Column, String, Enum, UUID, ForeignKey, Date, DateTime, func, Text, Numeric, Integer, Boolean, Time
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import BaseModel


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    RESERVED = "reserved"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    BOARDED = "boarded"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"
    PAYMENT_PENDING = "payment_pending"


class BookingSource(str, enum.Enum):
    WEBSITE = "website"
    WHATSAPP = "whatsapp"
    PHONE = "phone"
    WALKIN = "walkin"
    AGENT = "agent"
    OFFICE = "office"
    CORPORATE = "corporate"
    API = "api"


class Booking(BaseModel):
    __tablename__ = "bookings"

    reference = Column(String(30), unique=True, nullable=False, index=True)

    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("schedules.id"), nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)

    booking_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    number_of_passengers = Column(Integer, nullable=False, default=1)
    number_of_seats = Column(Integer, nullable=False, default=1)
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0)
    outstanding_balance = Column(Numeric(10, 2), default=0)

    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    source = Column(Enum(BookingSource), default=BookingSource.WEBSITE)

    pickup_location = Column(String(255))
    pickup_time = Column(Time)
    dropoff_location = Column(String(255))

    cancellation_reason = Column(Text)
    cancelled_at = Column(DateTime(timezone=True))
    cancelled_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    rescheduled_from = Column(UUID(as_uuid=True), nullable=True)
    rescheduled_to = Column(UUID(as_uuid=True), nullable=True)

    notes = Column(Text)
    internal_notes = Column(Text)

    checked_in_at = Column(DateTime(timezone=True))
    checked_in_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    boarded_at = Column(DateTime(timezone=True))
    boarded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    completed_at = Column(DateTime(timezone=True))

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    customer = relationship("Customer", back_populates="bookings")
    schedule = relationship("Schedule", back_populates="bookings")
    passengers = relationship("Passenger", back_populates="booking", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="booking")