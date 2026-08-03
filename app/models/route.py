from sqlalchemy import Column, String, ForeignKey ,UUID, Date, DateTime, func, Text, Boolean, Numeric, Interval
from sqlalchemy.orm import relationship
import uuid

from app.core.database import BaseModel


class Route(BaseModel):
    __tablename__ = "routes"

    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    origin_lat = Column(Numeric(10, 8))
    origin_lng = Column(Numeric(11, 8))
    dest_lat = Column(Numeric(10, 8))
    dest_lng = Column(Numeric(11, 8))

    distance_km = Column(Numeric(10, 2))
    estimated_duration = Column(Interval)
    base_price = Column(Numeric(10, 2), nullable=False)

    is_international = Column(Boolean, default=False)
    border_crossing = Column(String(255))
    waypoints = Column(Text)

    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    schedules = relationship("Schedule", back_populates="route")