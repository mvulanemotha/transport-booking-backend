# app/schemas/report.py
from pydantic import BaseModel, UUID4
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal


# ---------- KPI Overview ----------
class ReportOverview(BaseModel):
    total_bookings: int
    total_revenue: Decimal
    active_customers: int
    fleet_utilization: float


# ---------- Daily Trends ----------
class DailyTrend(BaseModel):
    date: date
    bookings: int
    revenue: Decimal


# ---------- Route Analysis ----------
class RouteReport(BaseModel):
    route_name: str
    bookings: int
    revenue: Decimal


# ---------- Payment Methods ----------
class PaymentMethodReport(BaseModel):
    method: str
    amount: Decimal
    percentage: float


# ---------- Fleet Utilization ----------
class VehicleUtilizationReport(BaseModel):
    vehicle_name: str
    utilization: float
    trips: int


# ---------- Customer Growth ----------
class CustomerGrowthReport(BaseModel):
    month: str
    customers: int


# ---------- Recent Booking ----------
class RecentBookingReport(BaseModel):
    id: UUID4
    reference: str
    customer: str
    route: str
    amount: Decimal
    status: str
    date: date


# ---------- Full Report (Overview Tab) ----------
class FullReportResponse(BaseModel):
    overview: ReportOverview
    booking_trends: List[DailyTrend]
    revenue_trends: List[DailyTrend]
    recent_bookings: List[RecentBookingReport]


# ---------- Aliases for backward compatibility ----------
# These satisfy imports from app/schemas/__init__.py
BookingReportResponse = FullReportResponse
FinancialReportResponse = FullReportResponse
FleetReportResponse = FullReportResponse
CustomerReportResponse = FullReportResponse