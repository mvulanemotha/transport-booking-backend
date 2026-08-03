from sqlalchemy import Column, String, Enum, UUID, ForeignKey, Date, DateTime, func, Text, Numeric, Boolean
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import BaseModel


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    MOMO = "momo"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    CORPORATE = "corporate"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Payment(BaseModel):
    __tablename__ = "payments"

    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0)
    outstanding_balance = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)

    method = Column(Enum(PaymentMethod), nullable=False)
    reference = Column(String(100), unique=True, nullable=False)
    transaction_id = Column(String(100), unique=True)

    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())

    gateway = Column(String(50))
    gateway_response = Column(Text)
    gateway_transaction_id = Column(String(255))

    refund_amount = Column(Numeric(10, 2), default=0)
    refund_date = Column(DateTime(timezone=True))
    refund_reason = Column(Text)
    refund_reference = Column(String(100))

    notes = Column(Text)
    internal_notes = Column(Text)
    receipt_number = Column(String(50))
    receipt_sent = Column(Boolean, default=False)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    booking = relationship("Booking", back_populates="payments")