from sqlalchemy import Column, String, Integer, Enum, UUID, ForeignKey, Date, Time, DateTime, func, Text, Numeric, Boolean
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class ScheduleStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    FULLY_BOOKED = "fully_booked"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)

    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    departure_location = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    departure_location_detail = Column(Text)
    destination_detail = Column(Text)

    departure_date = Column(Date, nullable=False, index=True)
    departure_time = Column(Time, nullable=False)
    estimated_arrival = Column(Time)

    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False)

    capacity = Column(Integer, nullable=False)
    booked_seats = Column(Integer, default=0, nullable=False)
    available_seats = Column(Integer, default=0)  # computed

    price = Column(Numeric(10, 2), nullable=False)
    dynamic_price = Column(Numeric(10, 2))
    surge_multiplier = Column(Numeric(3, 2), default=1.0)

    status = Column(Enum(ScheduleStatus), default=ScheduleStatus.SCHEDULED)

    is_holiday = Column(Boolean, default=False)
    is_peak = Column(Boolean, default=False)

    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True))
    cancellation_reason = Column(Text)
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    route = relationship("Route", back_populates="schedules")
    vehicle = relationship("Vehicle", back_populates="schedules")
    driver = relationship("Driver", back_populates="schedules")
    bookings = relationship("Booking", back_populates="schedule")