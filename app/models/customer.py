from sqlalchemy import Column, String, Integer, Numeric, Boolean, UUID, ForeignKey, Date, DateTime, func, Text, JSON
from sqlalchemy.orm import relationship
import uuid

from app.core.database import BaseModel


class Customer(BaseModel):
    __tablename__ = "customers"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, unique=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    id_number = Column(String(50))
    passport_number = Column(String(50))
    nationality = Column(String(100))
    address = Column(Text)
    date_of_birth = Column(Date)
    gender = Column(String(20))

    membership_plan = Column(String(50), default="basic")
    membership_start = Column(Date)
    membership_expiry = Column(Date)
    membership_discount = Column(Numeric(5, 2), default=0)

    loyalty_points = Column(Integer, default=0)
    total_trips = Column(Integer, default=0)
    total_spent = Column(Numeric(10, 2), default=0)
    average_rating = Column(Numeric(3, 2))

    preferred_pickup = Column(String(255))
    preferred_dropoff = Column(String(255))
    preferences = Column(JSON)

    #corporate_id = Column(UUID(as_uuid=True), ForeignKey("corporate_customers.id"), nullable=True)

    notes = Column(Text)
    internal_notes = Column(Text)
    tags = Column(JSON)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=True)
    whatsapp_notifications = Column(Boolean, default=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    bookings = relationship("Booking", back_populates="customer")
