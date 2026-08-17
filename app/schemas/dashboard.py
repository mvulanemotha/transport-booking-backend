# app/schemas/dashboard.py
from pydantic import BaseModel
from decimal import Decimal
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

class DailyBookingTrend(BaseModel):
    date: date
    bookings: int

class DailyRevenueTrend(BaseModel):
    date: date
    revenue: Decimal

class PopularRoute(BaseModel):
    route_name: str
    bookings: int

class VehicleUtilization(BaseModel):
    used: int      # vehicles assigned today
    available: int # vehicles with status = 'available'

class RecentActivity(BaseModel):
    id: UUID
    action: str
    time: datetime
    user: Optional[str] = None

class DashboardChartsData(BaseModel):
    booking_trends: List[DailyBookingTrend]
    revenue_trends: List[DailyRevenueTrend]
    popular_routes: List[PopularRoute]
    utilization: VehicleUtilization
    recent_activity: List[RecentActivity]

class KPIData(BaseModel):
    today_bookings: int
    today_departures: int
    fully_booked_trips: int
    monthly_revenue: Decimal
    active_customers: int
    available_seats: int
    pending_payments: int
    outstanding_payments: Decimal
    vehicles_assigned: int
    available_vehicles: int
    cancelled_bookings: int