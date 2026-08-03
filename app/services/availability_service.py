from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, date, timedelta
import uuid

from app.models.schedule import Schedule, ScheduleStatus
from app.models.booking import Booking, BookingStatus
from app.models.vehicle import Vehicle
from app.models.route import Route


class AvailabilityService:
    @staticmethod
    async def check_seat_availability(
        db: AsyncSession,
        schedule_id: str,
        requested_seats: int = 1
    ) -> Dict[str, Any]:
        """
        Check if requested seats are available on a schedule

        Returns:
            {
                "available": bool,
                "available_seats": int,
                "total_capacity": int,
                "booked_seats": int,
                "is_full": bool
            }
        """
        query = select(Schedule).where(Schedule.id == uuid.UUID(schedule_id))
        result = await db.execute(query)
        schedule = result.scalar_one_or_none()

        if not schedule:
            return {
                "available": False,
                "available_seats": 0,
                "total_capacity": 0,
                "booked_seats": 0,
                "is_full": True,
                "error": "Schedule not found"
            }

        available_seats = schedule.available_seats
        is_available = available_seats >= requested_seats

        return {
            "available": is_available,
            "available_seats": available_seats,
            "total_capacity": schedule.capacity,
            "booked_seats": schedule.booked_seats,
            "is_full": available_seats == 0,
            "schedule_code": schedule.code,
            "departure_date": schedule.departure_date,
            "departure_time": schedule.departure_time
        }

    @staticmethod
    async def get_next_available_schedule(
        db: AsyncSession,
        route_id: str,
        after_date: Optional[date] = None,
        min_seats: int = 1
    ) -> Optional[Schedule]:
        """
        Get the next available schedule for a route

        Args:
            route_id: The route to search for
            after_date: Search for schedules after this date (default: today)
            min_seats: Minimum number of seats required
        """
        if not after_date:
            after_date = date.today()

        query = select(Schedule).where(
            and_(
                Schedule.route_id == uuid.UUID(route_id),
                Schedule.departure_date >= after_date,
                Schedule.available_seats >= min_seats,
                Schedule.status == ScheduleStatus.SCHEDULED,
                Schedule.is_deleted.is_(None)
            )
        ).order_by(
            Schedule.departure_date,
            Schedule.departure_time
        ).limit(1)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_next_available_schedules(
        db: AsyncSession,
        route_id: str,
        after_date: Optional[date] = None,
        min_seats: int = 1,
        limit: int = 5
    ) -> List[Schedule]:
        """
        Get next available schedules for a route

        Args:
            route_id: The route to search for
            after_date: Search for schedules after this date (default: today)
            min_seats: Minimum number of seats required
            limit: Maximum number of schedules to return
        """
        if not after_date:
            after_date = date.today()

        query = select(Schedule).where(
            and_(
                Schedule.route_id == uuid.UUID(route_id),
                Schedule.departure_date >= after_date,
                Schedule.available_seats >= min_seats,
                Schedule.status == ScheduleStatus.SCHEDULED,
                Schedule.is_deleted.is_(None)
            )
        ).order_by(
            Schedule.departure_date,
            Schedule.departure_time
        ).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_schedule_occupancy(
        db: AsyncSession,
        schedule_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed occupancy information for a schedule
        """
        query = select(Schedule).where(Schedule.id == uuid.UUID(schedule_id))
        result = await db.execute(query)
        schedule = result.scalar_one_or_none()

        if not schedule:
            return {"error": "Schedule not found"}

        # Get confirmed bookings count
        confirmed_count = await db.execute(
            select(func.count()).select_from(Booking)
            .where(
                and_(
                    Booking.schedule_id == uuid.UUID(schedule_id),
                    Booking.status.in_([
                        BookingStatus.CONFIRMED,
                        BookingStatus.CHECKED_IN,
                        BookingStatus.BOARDED
                    ]),
                    Booking.is_deleted.is_(None)
                )
            )
        )
        confirmed_count = confirmed_count.scalar()

        # Get pending bookings count
        pending_count = await db.execute(
            select(func.count()).select_from(Booking)
            .where(
                and_(
                    Booking.schedule_id == uuid.UUID(schedule_id),
                    Booking.status == BookingStatus.PENDING,
                    Booking.is_deleted.is_(None)
                )
            )
        )
        pending_count = pending_count.scalar()

        return {
            "schedule_code": schedule.code,
            "total_capacity": schedule.capacity,
            "booked_seats": schedule.booked_seats,
            "available_seats": schedule.available_seats,
            "confirmed_bookings": confirmed_count,
            "pending_bookings": pending_count,
            "occupancy_percentage": round(
                (schedule.booked_seats / schedule.capacity) * 100, 2
            ) if schedule.capacity > 0 else 0,
            "is_full": schedule.available_seats == 0,
            "status": schedule.status
        }

    @staticmethod
    async def find_alternative_schedules(
        db: AsyncSession,
        schedule_id: str,
        min_seats: int = 1,
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Find alternative schedules for the same route when a schedule is full

        Args:
            schedule_id: The original schedule ID
            min_seats: Minimum seats required
            days_ahead: How many days ahead to search
        """
        # Get the original schedule
        query = select(Schedule).where(Schedule.id == uuid.UUID(schedule_id))
        result = await db.execute(query)
        original = result.scalar_one_or_none()

        if not original:
            return []

        # Calculate date range
        start_date = original.departure_date + timedelta(days=1)
        end_date = start_date + timedelta(days=days_ahead)

        # Find alternative schedules
        alternatives = await db.execute(
            select(Schedule)
            .where(
                and_(
                    Schedule.route_id == original.route_id,
                    Schedule.departure_date.between(start_date, end_date),
                    Schedule.available_seats >= min_seats,
                    Schedule.status == ScheduleStatus.SCHEDULED,
                    Schedule.is_deleted.is_(None),
                    Schedule.id != uuid.UUID(schedule_id)
                )
            )
            .order_by(
                Schedule.departure_date,
                Schedule.departure_time
            )
        )
        alternatives = alternatives.scalars().all()

        # Format results
        result = []
        for alt in alternatives:
            result.append({
                "id": str(alt.id),
                "code": alt.code,
                "departure_date": alt.departure_date,
                "departure_time": alt.departure_time,
                "available_seats": alt.available_seats,
                "price": alt.price,
                "is_peak": alt.is_peak,
                "is_holiday": alt.is_holiday
            })

        return result

    @staticmethod
    async def reserve_seats(
        db: AsyncSession,
        schedule_id: str,
        seats: int,
        booking_id: Optional[str] = None
    ) -> bool:
        """
        Reserve seats on a schedule (temporary hold)

        This is used to prevent double-booking while a customer is completing
        the booking process.
        """
        query = select(Schedule).where(Schedule.id == uuid.UUID(schedule_id))
        result = await db.execute(query)
        schedule = result.scalar_one_or_none()

        if not schedule:
            return False

        if schedule.available_seats < seats:
            return False

        # Reserve the seats
        schedule.booked_seats += seats
        schedule.available_seats = schedule.capacity - schedule.booked_seats

        # Update status if full
        if schedule.available_seats == 0:
            schedule.status = ScheduleStatus.FULLY_BOOKED

        await db.commit()
        return True

    @staticmethod
    async def release_seats(
        db: AsyncSession,
        schedule_id: str,
        seats: int
    ) -> bool:
        """
        Release reserved seats (when booking is cancelled or expires)
        """
        query = select(Schedule).where(Schedule.id == uuid.UUID(schedule_id))
        result = await db.execute(query)
        schedule = result.scalar_one_or_none()

        if not schedule:
            return False

        # Release the seats
        schedule.booked_seats -= seats
        schedule.available_seats = schedule.capacity - schedule.booked_seats

        # Update status if no longer full
        if schedule.available_seats > 0 and schedule.status == ScheduleStatus.FULLY_BOOKED:
            schedule.status = ScheduleStatus.SCHEDULED

        await db.commit()
        return True

    @staticmethod
    async def check_vehicle_availability_for_schedule(
        db: AsyncSession,
        vehicle_id: str,
        departure_date: date,
        departure_time: str
    ) -> bool:
        """
        Check if a vehicle is available for a specific date and time
        """
        # Check if vehicle already has a schedule at the same time
        query = select(Schedule).where(
            and_(
                Schedule.vehicle_id == uuid.UUID(vehicle_id),
                Schedule.departure_date == departure_date,
                Schedule.departure_time == departure_time,
                Schedule.status != ScheduleStatus.CANCELLED,
                Schedule.is_deleted.is_(None)
            )
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        return existing is None

    @staticmethod
    async def check_driver_availability_for_schedule(
        db: AsyncSession,
        driver_id: str,
        departure_date: date,
        departure_time: str
    ) -> bool:
        """
        Check if a driver is available for a specific date and time
        """
        # Check if driver already has a schedule at the same time
        query = select(Schedule).where(
            and_(
                Schedule.driver_id == uuid.UUID(driver_id),
                Schedule.departure_date == departure_date,
                Schedule.departure_time == departure_time,
                Schedule.status != ScheduleStatus.CANCELLED,
                Schedule.is_deleted.is_(None)
            )
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        return existing is None

    @staticmethod
    async def get_available_seats_summary(
        db: AsyncSession,
        route_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get a summary of available seats for a route over a date range
        """
        schedules = await db.execute(
            select(Schedule)
            .where(
                and_(
                    Schedule.route_id == uuid.UUID(route_id),
                    Schedule.departure_date.between(start_date, end_date),
                    Schedule.status != ScheduleStatus.CANCELLED,
                    Schedule.is_deleted.is_(None)
                )
            )
            .order_by(Schedule.departure_date, Schedule.departure_time)
        )
        schedules = schedules.scalars().all()

        summary = []
        for schedule in schedules:
            summary.append({
                "date": schedule.departure_date,
                "time": schedule.departure_time,
                "schedule_code": schedule.code,
                "total_seats": schedule.capacity,
                "available_seats": schedule.available_seats,
                "booked_seats": schedule.booked_seats,
                "is_full": schedule.available_seats == 0,
                "price": schedule.price,
                "status": schedule.status
            })

        return summary

    @staticmethod
    async def get_route_availability(
        db: AsyncSession,
        route_id: str,
        date_range: int = 7
    ) -> Dict[str, Any]:
        """
        Get availability summary for a route over the next N days
        """
        start_date = date.today()
        end_date = start_date + timedelta(days=date_range)

        schedules = await db.execute(
            select(Schedule)
            .where(
                and_(
                    Schedule.route_id == uuid.UUID(route_id),
                    Schedule.departure_date.between(start_date, end_date),
                    Schedule.status != ScheduleStatus.CANCELLED,
                    Schedule.is_deleted.is_(None)
                )
            )
            .order_by(Schedule.departure_date, Schedule.departure_time)
        )
        schedules = schedules.scalars().all()

        # Get route details
        route = await db.execute(
            select(Route).where(Route.id == uuid.UUID(route_id))
        )
        route = route.scalar_one_or_none()

        if not route:
            return {"error": "Route not found"}

        total_seats = 0
        total_available = 0
        daily_summary = {}

        for schedule in schedules:
            date_key = schedule.departure_date.isoformat()
            if date_key not in daily_summary:
                daily_summary[date_key] = {
                    "date": schedule.departure_date,
                    "schedules": [],
                    "total_seats": 0,
                    "available_seats": 0
                }

            daily_summary[date_key]["schedules"].append({
                "time": schedule.departure_time,
                "code": schedule.code,
                "available_seats": schedule.available_seats,
                "total_seats": schedule.capacity,
                "price": schedule.price,
                "is_full": schedule.available_seats == 0
            })

            daily_summary[date_key]["total_seats"] += schedule.capacity
            daily_summary[date_key]["available_seats"] += schedule.available_seats
            total_seats += schedule.capacity
            total_available += schedule.available_seats

        return {
            "route": {
                "id": str(route.id),
                "origin": route.origin,
                "destination": route.destination
            },
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_seats": total_seats,
            "total_available": total_available,
            "occupancy_rate": round(
                ((total_seats - total_available) / total_seats) * 100, 2
            ) if total_seats > 0 else 0,
            "daily_summary": list(daily_summary.values())
        }