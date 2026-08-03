from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PaymentBase(BaseModel):
    booking_id: str
    amount: Decimal = Field(..., ge=0)
    method: str
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    amount_paid: Optional[Decimal] = Field(None, ge=0)
    outstanding_balance: Optional[Decimal] = Field(None, ge=0)
    refund_amount: Optional[Decimal] = Field(None, ge=0)
    refund_date: Optional[datetime] = None
    refund_reason: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: str
    reference: str
    transaction_id: Optional[str] = None
    amount_paid: Decimal
    outstanding_balance: Decimal
    tax_amount: Decimal = Decimal('0')
    discount_amount: Decimal = Decimal('0')
    status: str
    payment_date: datetime
    gateway: Optional[str] = None
    gateway_response: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    refund_amount: Decimal = Decimal('0')
    refund_date: Optional[datetime] = None
    refund_reason: Optional[str] = None
    receipt_number: Optional[str] = None
    receipt_sent: bool = False
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int