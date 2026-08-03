from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from decimal import Decimal


# ==================== Corporate Customer Schemas ====================

class CorporateCustomerBase(BaseModel):
    """Base schema for corporate customer"""
    company_name: str = Field(..., min_length=2, max_length=255)
    registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=100)
    vat_number: Optional[str] = Field(None, max_length=100)
    contact_person: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=10, max_length=50)
    email: EmailStr
    website: Optional[str] = Field(None, max_length=255)
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)

    # Financial settings
    discount_rate: Decimal = Field(default=0, ge=0, le=100)
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    payment_terms: Optional[int] = Field(30, ge=1, le=365)
    default_payment_method: Optional[str] = Field(None, max_length=50)

    # Account features
    allow_multiple_bookings: bool = True
    allow_self_service: bool = True
    require_approval: bool = False
    custom_pricing: Optional[Dict[str, Any]] = None

    # Subscription
    subscription_plan: Optional[str] = Field(None, max_length=50)

    # Additional
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CorporateCustomerCreate(CorporateCustomerBase):
    """Schema for creating a corporate customer"""
    pass


class CorporateCustomerUpdate(BaseModel):
    """Schema for updating a corporate customer"""
    company_name: Optional[str] = Field(None, min_length=2, max_length=255)
    registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=100)
    vat_number: Optional[str] = Field(None, max_length=100)
    contact_person: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=50)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    discount_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    payment_terms: Optional[int] = Field(None, ge=1, le=365)
    default_payment_method: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    allow_multiple_bookings: Optional[bool] = None
    allow_self_service: Optional[bool] = None
    require_approval: Optional[bool] = None
    custom_pricing: Optional[Dict[str, Any]] = None
    subscription_plan: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CorporateCustomerResponse(CorporateCustomerBase):
    """Schema for corporate customer response"""
    id: str
    account_manager_id: Optional[str] = None
    credit_used: Decimal = Decimal('0')
    credit_available: Optional[Decimal] = None
    is_active: bool
    is_verified: bool
    verification_date: Optional[datetime] = None
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    auto_renew: bool = True
    total_bookings: int = 0
    total_spent: Decimal = Decimal('0')
    average_booking_value: Optional[Decimal] = None
    last_booking_date: Optional[datetime] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CorporateCustomerListResponse(BaseModel):
    """Schema for paginated corporate customer list"""
    items: List[CorporateCustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== Corporate User Schemas ====================

class CorporateUserBase(BaseModel):
    """Base schema for corporate user"""
    user_id: str
    role: str = Field(default="member", pattern="^(admin|manager|member|viewer)$")
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)

    # Permissions
    can_book: bool = True
    can_cancel: bool = True
    can_view_history: bool = True
    can_view_billing: bool = False
    can_manage_users: bool = False
    can_approve_bookings: bool = False
    can_view_reports: bool = False

    # Approval limits
    approval_limit: Decimal = Field(default=0, ge=0)
    requires_approval: bool = False


class CorporateUserCreate(CorporateUserBase):
    """Schema for creating a corporate user"""
    pass


class CorporateUserUpdate(BaseModel):
    """Schema for updating a corporate user"""
    role: Optional[str] = Field(None, pattern="^(admin|manager|member|viewer)$")
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    can_book: Optional[bool] = None
    can_cancel: Optional[bool] = None
    can_view_history: Optional[bool] = None
    can_view_billing: Optional[bool] = None
    can_manage_users: Optional[bool] = None
    can_approve_bookings: Optional[bool] = None
    can_view_reports: Optional[bool] = None
    approval_limit: Optional[Decimal] = Field(None, ge=0)
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None


class CorporateUserResponse(CorporateUserBase):
    """Schema for corporate user response"""
    id: str
    corporate_id: str
    invited_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Corporate Booking Agent Schemas ====================

class CorporateBookingAgentBase(BaseModel):
    """Base schema for corporate booking agent"""
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=50)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    is_primary: bool = False
    can_book: bool = True
    can_cancel: bool = True
    can_modify: bool = True


class CorporateBookingAgentCreate(CorporateBookingAgentBase):
    """Schema for creating a corporate booking agent"""
    corporate_id: str


class CorporateBookingAgentUpdate(BaseModel):
    """Schema for updating a corporate booking agent"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=50)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = None
    can_book: Optional[bool] = None
    can_cancel: Optional[bool] = None
    can_modify: Optional[bool] = None
    is_active: Optional[bool] = None


class CorporateBookingAgentResponse(CorporateBookingAgentBase):
    """Schema for corporate booking agent response"""
    id: str
    corporate_id: str
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Corporate Invoice Schemas ====================

class CorporateInvoiceItemBase(BaseModel):
    """Base schema for corporate invoice item"""
    description: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(1, ge=1)
    unit_price: Decimal = Field(..., ge=0)
    total_price: Decimal = Field(..., ge=0)
    booking_id: Optional[str] = None
    schedule_id: Optional[str] = None
    tax_rate: Decimal = Field(default=0, ge=0, le=100)
    tax_amount: Decimal = Field(default=0, ge=0)
    notes: Optional[str] = None


class CorporateInvoiceItemCreate(CorporateInvoiceItemBase):
    pass


class CorporateInvoiceItemResponse(CorporateInvoiceItemBase):
    """Schema for corporate invoice item response"""
    id: str
    invoice_id: str

    class Config:
        from_attributes = True


class CorporateInvoiceBase(BaseModel):
    """Base schema for corporate invoice"""
    invoice_number: str = Field(..., max_length=50)
    invoice_date: datetime
    due_date: Optional[datetime] = None
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=0, ge=0)
    discount_amount: Decimal = Field(default=0, ge=0)
    total_amount: Decimal = Field(..., ge=0)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class CorporateInvoiceCreate(CorporateInvoiceBase):
    """Schema for creating a corporate invoice"""
    corporate_id: str
    items: List[CorporateInvoiceItemCreate] = []


class CorporateInvoiceUpdate(BaseModel):
    """Schema for updating a corporate invoice"""
    status: Optional[str] = Field(None, pattern="^(draft|sent|paid|overdue|cancelled)$")
    due_date: Optional[datetime] = None
    amount_paid: Optional[Decimal] = Field(None, ge=0)
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_date: Optional[datetime] = None
    payment_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class CorporateInvoiceResponse(CorporateInvoiceBase):
    """Schema for corporate invoice response"""
    id: str
    corporate_id: str
    amount_paid: Decimal = Decimal('0')
    outstanding_balance: Decimal = Decimal('0')
    status: str
    payment_method: Optional[str] = None
    payment_date: Optional[datetime] = None
    payment_reference: Optional[str] = None
    created_by: str
    sent_by: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: List[CorporateInvoiceItemResponse] = []

    class Config:
        from_attributes = True


class CorporateInvoiceListResponse(BaseModel):
    """Schema for paginated corporate invoice list"""
    items: List[CorporateInvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== Corporate Statistics Schemas ====================

class CorporateStatistics(BaseModel):
    """Schema for corporate statistics"""
    corporate_id: str
    company_name: str
    total_bookings: int
    total_spent: Decimal
    average_booking_value: Decimal
    total_invoices: int
    paid_invoices: int
    overdue_invoices: int
    total_credit_used: Decimal
    credit_available: Decimal
    active_users: int
    last_booking_date: Optional[datetime] = None

    class Config:
        from_attributes = True