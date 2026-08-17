# app/services/report_service.py
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional , List
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import cast, Date, func
from app.schemas.report import DailyTrend

from app.models.booking import Booking, BookingStatus
from app.models.customer import Customer
from app.models.schedule import Schedule
from app.models.route import Route
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.report import CustomerGrowthReport
from app.models.payment import Payment  # if you have a Payment model, else derive from Booking

logger = logging.getLogger(__name__)

class ReportService:

    @staticmethod
    async def get_overview(
        db: AsyncSession,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> dict:
        """Compute overview KPIs for the given date range."""
        if not date_from:
            # default to last 30 days
            date_to = date_to or date.today()
            date_from = date_to - timedelta(days=30)
        if not date_to:
            date_to = date.today()

        # 1. Total bookings (non-cancelled) in range
        total_bookings = await db.scalar(
            select(func.count(Booking.id))
            .where(
                and_(
                    Booking.booking_date >= date_from,
                    Booking.booking_date <= date_to,
                    Booking.status != BookingStatus.CANCELLED
                )
            )
        ) or 0

        # 2. Total revenue in range (confirmed/completed)
        total_revenue = await db.scalar(
            select(func.sum(Booking.total_amount))
            .where(
                and_(
                    Booking.booking_date >= date_from,
                    Booking.booking_date <= date_to,
                    Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
                )
            )
        ) or Decimal(0)

        # 3. Active customers (all time, or within range)
        active_customers = await db.scalar(
            select(func.count(Customer.id))
            .where(Customer.is_active == True)
        ) or 0

        # 4. Fleet utilization: average of (booked_seats / capacity) across schedules in range
        # We'll compute per schedule and average
        schedules = await db.execute(
            select(Schedule.booked_seats, Schedule.capacity)
            .where(Schedule.departure_date.between(date_from, date_to))
        )
        rows = schedules.all()
        if rows:
            total_util = sum( (row.booked_seats / row.capacity) * 100 if row.capacity > 0 else 0 for row in rows )
            fleet_utilization = total_util / len(rows)
        else:
            fleet_utilization = 0.0

        return {
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "active_customers": active_customers,
            "fleet_utilization": round(fleet_utilization, 1)
        }

    @staticmethod
    async def get_route_analysis(
        db: AsyncSession,
        date_from: date,
        date_to: date
    ) -> List[dict]:
        """Aggregate bookings and revenue by route."""
        stmt = select(
            Route.origin,
            Route.destination,
            func.count(Booking.id).label("bookings"),
            func.sum(Booking.total_amount).label("revenue")
        ).join(Booking, Booking.route_id == Route.id)\
         .where(Booking.booking_date.between(date_from, date_to))\
         .group_by(Route.id, Route.origin, Route.destination)\
         .order_by(func.count(Booking.id).desc())

        result = await db.execute(stmt)
        rows = result.all()
        return [
            {
                "route_name": f"{row.origin} → {row.destination}",
                "bookings": row.bookings,
                "revenue": row.revenue or Decimal(0)
            }
            for row in rows
        ]

    @staticmethod
    async def get_payment_methods(
        db: AsyncSession,
        date_from: date,
        date_to: date
    ) -> List[dict]:
        """
        Distribution of payment methods.
        Assumes you have a Payment model with method and amount.
        If not, you can derive from Booking.source or a separate payment table.
        For demo, we'll use a dummy mapping from Booking.source.
        """
        # Assuming Booking has a 'source' field that can be 'cash', 'card', 'bank_transfer', 'momo', etc.
        # Or better, a Payment model. We'll simulate with a GROUP BY on source.
        stmt = select(
            Booking.source,
            func.sum(Booking.total_amount).label("amount")
        ).where(
            Booking.booking_date.between(date_from, date_to)
        ).group_by(Booking.source)

        result = await db.execute(stmt)
        rows = result.all()
        total = sum(row.amount for row in rows) or 1  # avoid division by zero
        return [
            {
                "method": row.source or "Unknown",
                "amount": row.amount or Decimal(0),
                "percentage": (row.amount / total) * 100 if total else 0
            }
            for row in rows
        ]

    @staticmethod
    async def get_fleet_utilization(
        db: AsyncSession,
        date_from: date,
        date_to: date
    ) -> List[dict]:
        """Utilization per vehicle over the date range."""
        # We'll count trips and average occupancy per vehicle
        stmt = select(
            Vehicle.registration,
            Vehicle.name,
            func.count(Schedule.id).label("trips"),
            func.avg(Schedule.booked_seats / Schedule.capacity * 100).label("utilization")
        ).join(Schedule, Schedule.vehicle_id == Vehicle.id)\
         .where(Schedule.departure_date.between(date_from, date_to))\
         .group_by(Vehicle.id, Vehicle.registration, Vehicle.name)\
         .order_by(func.avg(Schedule.booked_seats / Schedule.capacity * 100).desc())

        result = await db.execute(stmt)
        rows = result.all()
        return [
            {
                "vehicle_name": row.name or row.registration,
                "utilization": round(row.utilization or 0, 1),
                "trips": row.trips
            }
            for row in rows
        ]

    @staticmethod
    async def get_customer_growth(db: AsyncSession, months: int = 6) -> List[CustomerGrowthReport]:
        """Monthly customer growth for the last N months."""
        now = date.today()
        start_date = now - timedelta(days=months * 30)  # approximate, we'll adjust

        # Query: group by year and month
        stmt = select(
            func.extract('year', Customer.created_at).label("year"),
            func.extract('month', Customer.created_at).label("month"),
            func.count(Customer.id).label("count")
        ).where(Customer.created_at >= start_date)\
        .group_by("year", "month")\
        .order_by("year", "month")

        result = await db.execute(stmt)
        rows = result.all()

        # Build a dict: (year, month) -> count
        month_counts = {}
        for row in rows:
            year = int(row.year)   # ensure integer
            month = int(row.month) # ensure integer
            key = (year, month)
            month_counts[key] = month_counts.get(key, 0) + row.count

        # Generate full list of months from start_date to now
        current = start_date.replace(day=1)
        end = now.replace(day=1)
        reports = []
        while current <= end:
            key = (current.year, current.month)
            count = month_counts.get(key, 0)
            month_name = current.strftime("%b")  # "Jan", "Feb", etc.
            reports.append(CustomerGrowthReport(month=month_name, customers=count))
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return reports



    @staticmethod
    async def get_booking_trends(db: AsyncSession, date_from: date, date_to: date) -> List[DailyTrend]:
        stmt = select(
            cast(Booking.booking_date, Date).label("booking_date"),
            func.count(Booking.id).label("bookings"),
            func.sum(Booking.total_amount).label("revenue")
        ).where(
            Booking.booking_date.between(date_from, date_to)
        ).group_by(
            cast(Booking.booking_date, Date)
        ).order_by(
            cast(Booking.booking_date, Date)
        )
        result = await db.execute(stmt)
        rows = result.all()
        return [
            DailyTrend(
                date=row.booking_date,
                bookings=row.bookings,
                revenue=row.revenue or Decimal(0)
            )
            for row in rows
        ]

    @staticmethod
    async def get_recent_bookings(db: AsyncSession, limit: int = 5) -> List[dict]:
        stmt = select(
            Booking.id,
            Booking.reference,
            Customer.full_name.label("customer"),
            func.concat(Route.origin, ' → ', Route.destination).label("route"),
            Booking.total_amount.label("amount"),
            Booking.status,
            cast(Booking.booking_date, Date).label("date")
        ).join(Customer, Booking.customer_id == Customer.id)\
        .join(Route, Booking.route_id == Route.id)\
        .order_by(Booking.booking_date.desc(), Booking.created_at.desc())\
        .limit(limit)
        result = await db.execute(stmt)
        rows = result.all()
        return [
            {
                "id": row.id,
                "reference": row.reference,
                "customer": row.customer,
                "route": row.route,
                "amount": row.amount,
                "status": row.status,
                "date": row.date
            }
            for row in rows
        ]