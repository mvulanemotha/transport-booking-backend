from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal


# ==================== Booking Report Schemas ====================

class BookingReportSummary(BaseModel):
    """Summary statistics for booking report"""
    total_bookings: int = 0
    total_revenue: Decimal = Decimal('0')
    average_booking_value: Decimal = Decimal('0')
    confirmed: int = 0
    cancelled: int = 0
    completed: int = 0
    pending: int = 0
    no_show: int = 0


class BookingReportItem(BaseModel):
    """Individual booking record in report"""
    reference: str
    customer_name: str
    customer_phone: Optional[str] = None
    route: str
    departure_date: date
    departure_time: str
    passengers: int
    amount: Decimal
    status: str
    source: str
    created_at: datetime


class RouteBookingStats(BaseModel):
    """Booking statistics by route"""
    route: str
    booking_count: int
    revenue: Decimal
    average_booking_value: Decimal
    cancellation_rate: float


class BookingReportResponse(BaseModel):
    """Complete booking report response"""
    date_range: Dict[str, str]
    summary: BookingReportSummary
    by_route: List[RouteBookingStats]
    by_status: Dict[str, int]
    by_source: Dict[str, int]
    daily_breakdown: List[Dict[str, Any]]
    recent_bookings: List[BookingReportItem]
    generated_at: datetime


# ==================== Financial Report Schemas ====================

class FinancialSummary(BaseModel):
    """Summary statistics for financial report"""
    total_revenue: Decimal = Decimal('0')
    total_payments: Decimal = Decimal('0')
    outstanding_payments: Decimal = Decimal('0')
    total_refunds: Decimal = Decimal('0')
    net_revenue: Decimal = Decimal('0')
    total_transactions: int = 0


class PaymentMethodStats(BaseModel):
    """Payment statistics by method"""
    method: str
    count: int
    total: Decimal
    percentage: float


class DailyRevenueStats(BaseModel):
    """Daily revenue breakdown"""
    date: date
    revenue: Decimal
    bookings: int
    average_booking: Decimal


class FinancialReportResponse(BaseModel):
    """Complete financial report response"""
    date_range: Dict[str, str]
    summary: FinancialSummary
    by_method: List[PaymentMethodStats]
    daily_breakdown: List[DailyRevenueStats]
    outstanding_invoices: List[Dict[str, Any]]
    generated_at: datetime


# ==================== Fleet Report Schemas ====================

class FleetSummary(BaseModel):
    """Summary statistics for fleet report"""
    total_vehicles: int = 0
    available: int = 0
    assigned: int = 0
    in_transit: int = 0
    maintenance: int = 0
    inactive: int = 0
    average_utilization: float = 0.0


class VehicleUtilizationStats(BaseModel):
    """Vehicle utilization statistics"""
    vehicle_id: str
    vehicle_name: str
    registration: str
    vehicle_type: str
    capacity: int
    total_trips: int
    completed_trips: int
    total_passengers: int
    total_revenue: Decimal
    utilization_rate: float
    maintenance_count: int
    last_maintenance: Optional[date]
    next_maintenance: Optional[date]


class FleetReportResponse(BaseModel):
    """Complete fleet report response"""
    summary: FleetSummary
    vehicles: List[VehicleUtilizationStats]
    by_type: Dict[str, Dict[str, Any]]
    by_status: Dict[str, int]
    generated_at: datetime


# ==================== Driver Report Schemas ====================

class DriverSummary(BaseModel):
    """Summary statistics for driver report"""
    total_drivers: int = 0
    active: int = 0
    on_leave: int = 0
    suspended: int = 0
    total_trips: int = 0
    total_passengers: int = 0
    average_rating: float = 0.0


class DriverPerformanceStats(BaseModel):
    """Driver performance statistics"""
    driver_id: str
    driver_name: str
    phone: str
    license_number: str
    trips_completed: int
    total_passengers: int
    total_earnings: Decimal
    rating: float
    on_time_rate: float
    license_expiry: date
    status: str


class DriverReportResponse(BaseModel):
    """Complete driver report response"""
    summary: DriverSummary
    drivers: List[DriverPerformanceStats]
    top_rated: List[DriverPerformanceStats]
    most_active: List[DriverPerformanceStats]
    generated_at: datetime


# ==================== Customer Report Schemas ====================

class CustomerSummary(BaseModel):
    """Summary statistics for customer report"""
    total_customers: int = 0
    active: int = 0
    new_customers: int = 0
    returning_customers: int = 0
    total_revenue: Decimal = Decimal('0')
    average_spent: Decimal = Decimal('0')
    loyalty_points_total: int = 0


class CustomerStats(BaseModel):
    """Customer statistics"""
    customer_id: str
    name: str
    phone: str
    email: Optional[str] = None
    membership_plan: str
    total_bookings: int
    total_spent: Decimal
    average_booking: Decimal
    loyalty_points: int
    last_booking_date: Optional[datetime]
    join_date: datetime
    is_active: bool


class CustomerReportResponse(BaseModel):
    """Complete customer report response"""
    date_range: Dict[str, str]
    summary: CustomerSummary
    top_customers: List[CustomerStats]
    new_customers: List[CustomerStats]
    by_membership: Dict[str, Dict[str, Any]]
    generated_at: datetime


# ==================== Route Report Schemas ====================

class RouteSummary(BaseModel):
    """Summary statistics for route report"""
    total_routes: int = 0
    active_routes: int = 0
    total_bookings: int = 0
    total_revenue: Decimal = Decimal('0')
    average_occupancy: float = 0.0


class RoutePerformanceStats(BaseModel):
    """Route performance statistics"""
    route_id: str
    route_code: str
    origin: str
    destination: str
    total_schedules: int
    total_bookings: int
    total_passengers: int
    total_revenue: Decimal
    average_occupancy: float
    cancellation_rate: float
    is_active: bool


class RouteReportResponse(BaseModel):
    """Complete route report response"""
    date_range: Dict[str, str]
    summary: RouteSummary
    routes: List[RoutePerformanceStats]
    top_routes: List[RoutePerformanceStats]
    by_status: Dict[str, int]
    generated_at: datetime


# ==================== Revenue Report Schemas ====================

class RevenueSummary(BaseModel):
    """Summary statistics for revenue report"""
    total_revenue: Decimal = Decimal('0')
    total_bookings: int = 0
    total_passengers: int = 0
    average_booking_value: Decimal = Decimal('0')
    revenue_per_passenger: Decimal = Decimal('0')


class RevenueBreakdown(BaseModel):
    """Revenue breakdown by category"""
    category: str
    amount: Decimal
    percentage: float
    booking_count: int


class RevenueTrend(BaseModel):
    """Revenue trend over time"""
    period: str
    revenue: Decimal
    bookings: int
    passengers: int


class RevenueReportResponse(BaseModel):
    """Complete revenue report response"""
    date_range: Dict[str, str]
    summary: RevenueSummary
    by_route: List[RevenueBreakdown]
    by_month: List[RevenueTrend]
    by_day: List[RevenueTrend]
    generated_at: datetime


# ==================== Report Filter Schemas ====================

class ReportFilters(BaseModel):
    """Filters for generating reports"""
    start_date: date
    end_date: date
    report_type: str = Field(..., pattern="^(booking|financial|fleet|driver|customer|route|revenue)$")
    route_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    customer_id: Optional[str] = None
    status: Optional[str] = None
    format: Optional[str] = Field("json", pattern="^(json|csv|excel|pdf)$")


class ReportExportResponse(BaseModel):
    """Response for report export"""
    report_type: str
    format: str
    filename: str
    content: str  # Base64 encoded or file path
    generated_at: datetime
    file_size: Optional[int] = None