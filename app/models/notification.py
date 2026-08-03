from sqlalchemy import Column, String, Boolean, UUID, ForeignKey, DateTime, func, Text, JSON, Integer
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import BaseModel


class NotificationType(str, enum.Enum):
    BOOKING_CONFIRMATION = "booking_confirmation"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_REMINDER = "payment_reminder"
    SCHEDULE_CHANGE = "schedule_change"
    VEHICLE_CHANGE = "vehicle_change"
    DRIVER_CHANGE = "driver_change"
    CANCELLATION = "cancellation"
    RESCHEDULE = "reschedule"
    REMINDER = "reminder"
    CHECK_IN = "check_in"
    BOARDING = "boarding"
    DELAY = "delay"
    PROMOTIONAL = "promotional"
    SYSTEM = "system"
    ALERT = "alert"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    IN_APP = "in_app"


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    recipient = Column(String(255))

    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    data = Column(JSON)

    channel = Column(String(50), nullable=False)
    template_id = Column(String(100))

    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True))
    read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))

    delivery_status = Column(String(50))
    delivery_error = Column(Text)
    retry_count = Column(Integer, default=0)
    scheduled_for = Column(DateTime(timezone=True))

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    customer = relationship("Customer", foreign_keys=[customer_id])