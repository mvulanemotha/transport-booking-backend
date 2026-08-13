from sqlalchemy import Column, String, Boolean, UUID, ForeignKey, Date, DateTime, func, Text, Numeric, Interval
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    origin_lat = Column(Numeric(10, 8), nullable=True)
    origin_lng = Column(Numeric(11, 8), nullable=True)
    dest_lat = Column(Numeric(10, 8), nullable=True)
    dest_lng = Column(Numeric(11, 8), nullable=True)

    distance_km = Column(Numeric(10, 2), nullable=True)
    estimated_duration = Column(Interval, nullable=True)  # In minutes
    base_price = Column(Numeric(10, 2), nullable=False)

    is_international = Column(Boolean, default=False)
    border_crossing = Column(String(255), nullable=True)
    waypoints = Column(Text, nullable=True)  # JSON array of waypoints

    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    schedules = relationship("Schedule", back_populates="route")