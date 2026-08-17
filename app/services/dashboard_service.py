# app/services/dashboard_service.py
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking, BookingStatus
from app.models.schedule import Schedule, ScheduleStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.customer import Customer

from typing import List

from app.models.route import Route
from app.schemas.dashboard import (
    DailyBookingTrend, DailyRevenueTrend, PopularRoute,
    VehicleUtilization, RecentActivity
)


logger = logging.getLogger(__name__)


class DashboardService:

    @staticmethod
    async def get_kpi_data(db: AsyncSession) -> dict:
        """
        Compute all KPI metrics for the dashboard.
        Returns a dictionary with keys matching the schema.
        """
        today = date.today()
        first_day_of_month = today.replace(day=1)

        # 1. Today's bookings (not cancelled)
        today_bookings_query = select(func.count()).select_from(Booking).where(
            and_(
                Booking.booking_date >= today,
                Booking.booking_date < today + timedelta(days=1),
                Booking.status != BookingStatus.CANCELLED
            )
        )
        today_bookings = await db.scalar(today_bookings_query) or 0

        # 2. Today's departures (scheduled or in_progress)
        today_departures_query = select(func.count()).select_from(Schedule).where(
            and_(
                Schedule.departure_date == today,
                Schedule.status.in_([ScheduleStatus.SCHEDULED, ScheduleStatus.IN_PROGRESS])
            )
        )
        today_departures = await db.scalar(today_departures_query) or 0

        # 3. Fully booked trips today
        fully_booked_query = select(func.count()).select_from(Schedule).where(
            and_(
                Schedule.departure_date == today,
                Schedule.available_seats == 0
            )
        )
        fully_booked_trips = await db.scalar(fully_booked_query) or 0

        # 4. Monthly revenue (sum of total_amount for confirmed/completed bookings this month)
        monthly_revenue_query = select(func.sum(Booking.total_amount)).select_from(Booking).where(
            and_(
                Booking.booking_date >= first_day_of_month,
                Booking.booking_date < first_day_of_month + timedelta(days=32),  # covers whole month
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
            )
        )
        monthly_revenue = await db.scalar(monthly_revenue_query) or Decimal(0)

        # 5. Active customers (is_active = True)
        active_customers_query = select(func.count()).select_from(Customer).where(Customer.is_active == True)
        active_customers = await db.scalar(active_customers_query) or 0

        # 6. Available seats across today's trips
        available_seats_query = select(func.sum(Schedule.available_seats)).select_from(Schedule).where(
            Schedule.departure_date == today
        )
        available_seats = await db.scalar(available_seats_query) or 0

        # 7. Pending payments (count of bookings with outstanding_balance > 0)
        pending_payments_query = select(func.count()).select_from(Booking).where(
            Booking.outstanding_balance > 0
        )
        pending_payments = await db.scalar(pending_payments_query) or 0

        # 8. Outstanding payments (sum of outstanding_balance)
        outstanding_payments_query = select(func.sum(Booking.outstanding_balance)).select_from(Booking).where(
            Booking.outstanding_balance > 0
        )
        outstanding_payments = await db.scalar(outstanding_payments_query) or Decimal(0)

        # 9. Vehicles assigned to trips today (distinct)
        vehicles_assigned_query = select(func.count(func.distinct(Schedule.vehicle_id))).select_from(Schedule).where(
            Schedule.departure_date == today
        )
        vehicles_assigned = await db.scalar(vehicles_assigned_query) or 0

        # 10. Available vehicles (status = 'available')
        available_vehicles_query = select(func.count()).select_from(Vehicle).where(
            Vehicle.status == VehicleStatus.AVAILABLE
        )
        available_vehicles = await db.scalar(available_vehicles_query) or 0

        # 11. Cancelled bookings this month
        cancelled_bookings_query = select(func.count()).select_from(Booking).where(
            and_(
                Booking.booking_date >= first_day_of_month,
                Booking.booking_date < first_day_of_month + timedelta(days=32),
                Booking.status == BookingStatus.CANCELLED
            )
        )
        cancelled_bookings = await db.scalar(cancelled_bookings_query) or 0

        return {
            "today_bookings": today_bookings,
            "today_departures": today_departures,
            "fully_booked_trips": fully_booked_trips,
            "monthly_revenue": monthly_revenue,
            "active_customers": active_customers,
            "available_seats": available_seats,
            "pending_payments": pending_payments,
            "outstanding_payments": outstanding_payments,
            "vehicles_assigned": vehicles_assigned,
            "available_vehicles": available_vehicles,
            "cancelled_bookings": cancelled_bookings,
        }


    @staticmethod
    async def get_booking_trends(db: AsyncSession) -> List[DailyBookingTrend]:
        """Daily bookings for the last 7 days (including today)."""
        today = date.today()
        start = today - timedelta(days=6)
        stmt = (
            select(Booking.booking_date, func.count(Booking.id))
            .where(Booking.booking_date >= start)
            .group_by(Booking.booking_date)
            .order_by(Booking.booking_date)
        )
        result = await db.execute(stmt)
        rows = result.all()
        counts = {row[0]: row[1] for row in rows}
        trends = []
        for i in range(7):
            d = start + timedelta(days=i)
            trends.append(DailyBookingTrend(date=d, bookings=counts.get(d, 0)))
        return trends

    @staticmethod
    async def get_revenue_trends(db: AsyncSession) -> List[DailyRevenueTrend]:
        """Daily revenue for the last 7 days."""
        today = date.today()
        start = today - timedelta(days=6)
        stmt = (
            select(Booking.booking_date, func.sum(Booking.total_amount))
            .where(Booking.booking_date >= start)
            .group_by(Booking.booking_date)
            .order_by(Booking.booking_date)
        )
        result = await db.execute(stmt)
        rows = result.all()
        rev_dict = {row[0]: row[1] or Decimal(0) for row in rows}
        trends = []
        for i in range(7):
            d = start + timedelta(days=i)
            trends.append(DailyRevenueTrend(date=d, revenue=rev_dict.get(d, Decimal(0))))
        return trends

    @staticmethod
    async def get_popular_routes(db: AsyncSession, limit: int = 4) -> List[PopularRoute]:
        """Top routes by bookings this month."""
        today = date.today()
        first_day = today.replace(day=1)
        stmt = (
            select(
                Route.origin,
                Route.destination,
                func.count(Booking.id).label("cnt")
            )
            .join(Booking, Booking.route_id == Route.id)
            .where(Booking.booking_date >= first_day)
            .group_by(Route.id, Route.origin, Route.destination)
            .order_by(func.count(Booking.id).desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.all()
        return [
            PopularRoute(route_name=f"{row[0]} → {row[1]}", bookings=row[2])
            for row in rows
        ]

    @staticmethod
    async def get_vehicle_utilization(db: AsyncSession) -> VehicleUtilization:
        """Count vehicles assigned today vs. available fleet."""
        today = date.today()
        # distinct vehicles assigned to schedules departing today
        assigned_stmt = select(func.count(func.distinct(Schedule.vehicle_id))).where(
            Schedule.departure_date == today
        )
        assigned = await db.scalar(assigned_stmt) or 0

        # vehicles with status = 'available' (adjust enum value if needed)
        available_stmt = select(func.count()).where(Vehicle.status == VehicleStatus.AVAILABLE)
        available = await db.scalar(available_stmt) or 0

        return VehicleUtilization(used=assigned, available=available)

    @staticmethod
    async def get_recent_activity(db: AsyncSession, limit: int = 5) -> List[RecentActivity]:
        """Latest 5 bookings with customer name."""
        stmt = (
            select(
                Booking.id,
                Booking.reference,
                Booking.created_at,
                Customer.full_name.label("customer_name")
            )
            .join(Customer, Booking.customer_id == Customer.id)
            .order_by(Booking.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.all()
        activities = []
        for row in rows:
            action = f"{row.customer_name} created booking {row.reference}"
            activities.append(
                RecentActivity(
                    id=row.id,
                    action=action,
                    time=row.created_at,
                    user=row.customer_name
                )
            )
        return activities