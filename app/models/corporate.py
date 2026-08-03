from sqlalchemy import Column, String, Boolean, UUID, ForeignKey, DateTime, func, Text, Numeric, JSON, Integer
from sqlalchemy.orm import relationship
import uuid

from app.core.database import BaseModel


class CorporateCustomer(BaseModel):
    """Corporate customer account model"""
    __tablename__ = "corporate_customers"

    # Company details
    company_name = Column(String(255), nullable=False, unique=True, index=True)
    registration_number = Column(String(100), unique=True)
    tax_id = Column(String(100))
    vat_number = Column(String(100))

    # Contact information
    contact_person = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    website = Column(String(255))

    # Address
    billing_address = Column(Text)
    shipping_address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))

    # Financial settings
    discount_rate = Column(Numeric(5, 2), default=0)
    credit_limit = Column(Numeric(10, 2))
    credit_used = Column(Numeric(10, 2), default=0)
    credit_available = Column(Numeric(10, 2))
    payment_terms = Column(Integer)  # Days
    default_payment_method = Column(String(50))

    # Account management
    account_manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime(timezone=True))

    # Account features
    allow_multiple_bookings = Column(Boolean, default=True)
    allow_self_service = Column(Boolean, default=True)
    require_approval = Column(Boolean, default=False)
    custom_pricing = Column(JSON)  # Custom pricing rules

    # Subscription
    subscription_plan = Column(String(50))
    subscription_start = Column(DateTime(timezone=True))
    subscription_end = Column(DateTime(timezone=True))
    auto_renew = Column(Boolean, default=True)

    # Statistics
    total_bookings = Column(Integer, default=0)
    total_spent = Column(Numeric(10, 2), default=0)
    average_booking_value = Column(Numeric(10, 2))
    last_booking_date = Column(DateTime(timezone=True))

    # Additional
    notes = Column(Text)
    internal_notes = Column(Text)
    tags = Column(JSON)  # Array of tags

    # Relationships
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relations
    account_manager = relationship("User", foreign_keys=[account_manager_id])
    creator = relationship("User", foreign_keys=[created_by])
    customers = relationship("Customer", back_populates="corporate")
    corporate_users = relationship("CorporateUser", back_populates="corporate")
    booking_agents = relationship("CorporateBookingAgent", back_populates="corporate")


class CorporateUser(BaseModel):
    """Users associated with a corporate account"""
    __tablename__ = "corporate_users"

    corporate_id = Column(UUID(as_uuid=True), ForeignKey("corporate_customers.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # User permissions within corporate account
    role = Column(String(50), default="member")  # admin, manager, member, viewer
    department = Column(String(100))
    job_title = Column(String(100))

    # Permissions
    can_book = Column(Boolean, default=True)
    can_cancel = Column(Boolean, default=True)
    can_view_history = Column(Boolean, default=True)
    can_view_billing = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    can_approve_bookings = Column(Boolean, default=False)
    can_view_reports = Column(Boolean, default=False)

    # Approval limits
    approval_limit = Column(Numeric(10, 2), default=0)
    requires_approval = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    invited_at = Column(DateTime(timezone=True))
    accepted_at = Column(DateTime(timezone=True))

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    corporate = relationship("CorporateCustomer", back_populates="corporate_users")
    user = relationship("User")


class CorporateBookingAgent(BaseModel):
    """Booking agents/contacts for corporate accounts"""
    __tablename__ = "corporate_booking_agents"

    corporate_id = Column(UUID(as_uuid=True), ForeignKey("corporate_customers.id"), nullable=False)

    # Agent details
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50))
    email = Column(String(255))
    department = Column(String(100))
    job_title = Column(String(100))

    # Permissions
    is_primary = Column(Boolean, default=False)
    can_book = Column(Boolean, default=True)
    can_cancel = Column(Boolean, default=True)
    can_modify = Column(Boolean, default=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    corporate = relationship("CorporateCustomer", back_populates="booking_agents")


class CorporateInvoice(BaseModel):
    """Invoices for corporate accounts"""
    __tablename__ = "corporate_invoices"

    corporate_id = Column(UUID(as_uuid=True), ForeignKey("corporate_customers.id"), nullable=False)

    # Invoice details
    invoice_number = Column(String(50), unique=True, nullable=False)
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True))

    # Amounts
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0)
    outstanding_balance = Column(Numeric(10, 2), default=0)

    # Status
    status = Column(String(50), default="draft")  # draft, sent, paid, overdue, cancelled

    # Payment
    payment_method = Column(String(50))
    payment_date = Column(DateTime(timezone=True))
    payment_reference = Column(String(100))

    # Period
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))

    # Additional
    notes = Column(Text)
    internal_notes = Column(Text)

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sent_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    sent_at = Column(DateTime(timezone=True))

    # Relationships
    corporate = relationship("CorporateCustomer")
    invoice_items = relationship("CorporateInvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class CorporateInvoiceItem(BaseModel):
    """Individual items on a corporate invoice"""
    __tablename__ = "corporate_invoice_items"

    invoice_id = Column(UUID(as_uuid=True), ForeignKey("corporate_invoices.id"), nullable=False)

    # Item details
    description = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

    # Reference
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=True)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("schedules.id"), nullable=True)

    # Tax
    tax_rate = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)

    # Additional
    notes = Column(Text)

    # Relationships
    invoice = relationship("CorporateInvoice", back_populates="invoice_items")
    booking = relationship("Booking")
    schedule = relationship("Schedule")