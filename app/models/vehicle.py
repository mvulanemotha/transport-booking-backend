from sqlalchemy import Column, String, Integer, Enum, UUID, ForeignKey, Date, DateTime, func, Text, Numeric, Boolean
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import BaseModel


class VehicleStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class VehicleType(str, enum.Enum):
    MINI_BUS = "mini_bus"
    BUS = "bus"
    VAN = "van"
    COACH = "coach"


class Vehicle(BaseModel):
    __tablename__ = "vehicles"

    registration = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100))
    vehicle_type = Column(Enum(VehicleType), nullable=False)
    capacity = Column(Integer, nullable=False)
    color = Column(String(50))
    make = Column(String(100))
    model = Column(String(100))
    year = Column(Integer)

    insurance_provider = Column(String(100))
    insurance_number = Column(String(100))
    insurance_expiry = Column(Date)

    license_number = Column(String(100))
    license_expiry = Column(Date)

    roadworthy_certificate = Column(String(100))
    roadworthy_expiry = Column(Date)

    status = Column(Enum(VehicleStatus), default=VehicleStatus.AVAILABLE, nullable=False)

    last_maintenance = Column(Date)
    next_maintenance = Column(Date)
    maintenance_notes = Column(Text)

    fuel_type = Column(String(50))
    fuel_efficiency = Column(Numeric(10, 2))
    tracking_device_id = Column(String(100))
    gps_enabled = Column(Boolean, default=False)

    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    schedules = relationship("Schedule", back_populates="vehicle")