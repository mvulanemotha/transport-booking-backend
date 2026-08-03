from sqlalchemy import Column, Integer , String, Enum, UUID, ForeignKey, Date, DateTime, func, Text, Boolean, Numeric
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import BaseModel


class DriverStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ON_LEAVE = "on_leave"


class Driver(BaseModel):
    __tablename__ = "drivers"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    address = Column(Text)
    date_of_birth = Column(Date)

    license_number = Column(String(100), unique=True, nullable=False)
    license_class = Column(String(50), nullable=False)
    license_expiry = Column(Date, nullable=False)
    license_issued = Column(Date)

    medical_expiry = Column(Date)
    passport_number = Column(String(50))
    passport_expiry = Column(Date)
    id_number = Column(String(50))

    emergency_contact = Column(String(255))
    emergency_phone = Column(String(50))

    is_available = Column(Boolean, default=True)
    status = Column(Enum(DriverStatus), default=DriverStatus.ACTIVE)

    trips_completed = Column(Integer, default=0)
    rating = Column(Numeric(3, 2), default=5.0)
    total_earnings = Column(Numeric(10, 2), default=0)

    hire_date = Column(Date)
    contract_end = Column(Date)
    languages = Column(String(255))
    specialties = Column(String(255))

    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    schedules = relationship("Schedule", back_populates="driver")