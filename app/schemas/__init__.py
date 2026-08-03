from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse
from app.schemas.corporate import (
    CorporateCustomerCreate, CorporateCustomerUpdate, CorporateCustomerResponse,
    CorporateUserCreate, CorporateUserUpdate, CorporateUserResponse,
    CorporateInvoiceCreate, CorporateInvoiceUpdate, CorporateInvoiceResponse
)
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleListResponse
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse, DriverListResponse
from app.schemas.route import RouteCreate, RouteUpdate, RouteResponse, RouteListResponse
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleListResponse
from app.schemas.booking import BookingCreate, BookingUpdate, BookingResponse, BookingListResponse
from app.schemas.passenger import PassengerCreate, PassengerUpdate, PassengerResponse
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse, PaymentListResponse
from app.schemas.audit import AuditLogResponse, AuditLogListResponse
from app.schemas.report import (
    BookingReportResponse,
    FinancialReportResponse,
    FleetReportResponse,
    DriverReportResponse,
    CustomerReportResponse,
    RouteReportResponse,
    RevenueReportResponse,
    ReportFilters,
    ReportExportResponse,
)

__all__ = [
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    # Role
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    # Customer
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerListResponse",
    # Corporate
    "CorporateCustomerCreate",
    "CorporateCustomerUpdate",
    "CorporateCustomerResponse",
    "CorporateUserCreate",
    "CorporateUserUpdate",
    "CorporateUserResponse",
    "CorporateInvoiceCreate",
    "CorporateInvoiceUpdate",
    "CorporateInvoiceResponse",
    # Vehicle
    "VehicleCreate",
    "VehicleUpdate",
    "VehicleResponse",
    "VehicleListResponse",
    # Driver
    "DriverCreate",
    "DriverUpdate",
    "DriverResponse",
    "DriverListResponse",
    # Route
    "RouteCreate",
    "RouteUpdate",
    "RouteResponse",
    "RouteListResponse",
    # Schedule
    "ScheduleCreate",
    "ScheduleUpdate",
    "ScheduleResponse",
    "ScheduleListResponse",
    # Booking
    "BookingCreate",
    "BookingUpdate",
    "BookingResponse",
    "BookingListResponse",
    # Passenger
    "PassengerCreate",
    "PassengerUpdate",
    "PassengerResponse",
    # Payment
    "PaymentCreate",
    "PaymentUpdate",
    "PaymentResponse",
    "PaymentListResponse",
    # Audit
    "AuditLogResponse",
    "AuditLogListResponse",
    # Report
    "BookingReportResponse",
    "FinancialReportResponse",
    "FleetReportResponse",
    "DriverReportResponse",
    "CustomerReportResponse",
    "RouteReportResponse",
    "RevenueReportResponse",
    "ReportFilters",
    "ReportExportResponse",
]