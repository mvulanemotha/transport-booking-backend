from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, date
import uuid

from app.models.schedule import Schedule, ScheduleStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.driver import Driver
from app.models.route import Route
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


class ScheduleService:
    @staticmethod
    async def create_schedule(
        db: AsyncSession,
        schedule_data: ScheduleCreate,
        user_id: str
    ) -> Schedule:
        """Create a new schedule"""
        # Check if vehicle is available
        vehicle = await db.execute(
            select(Vehicle).where(Vehicle.id == schedule_data.vehicle_id)
        )
        vehicle = vehicle.scalar_one_or_none()
        if not vehicle or vehicle.status != VehicleStatus.AVAILABLE:
            raise ValueError("Vehicle not available")

        # Check if driver is available
        driver = await db.execute(
            select(Driver).where(Driver.id == schedule_data.driver_id)
        )
        driver = driver.scalar_one_or_none()
        if not driver or not driver.is_available:
            raise ValueError("Driver not available")

        # Check for conflicts (vehicle or driver already booked)
        conflict = await db.execute(
            select(Schedule).where(
                and_(
                    Schedule.departure_date == schedule_data.departure_date,
                    or_(
                        Schedule.vehicle_id == schedule_data.vehicle_id,
                        Schedule.driver_id == schedule_data.driver_id
                    )
                )
            )
        )
        if conflict.scalar_one_or_none():
            raise ValueError("Vehicle or driver already scheduled for this date")

        # Generate schedule code
        today = date.today()
        count = await db.execute(
            select(func.count()).select_from(Schedule)
            .where(Schedule.created_at >= today)
        )
        count = count.scalar() + 1
        code = f"SCH-{today.strftime('%Y%m%d')}-{str(count).zfill(3)}"

        # Create schedule
        schedule = Schedule(
            code=code,
            route_id=schedule_data.route_id,
            departure_location=schedule_data.departure_location,
            destination=schedule_data.destination,
            departure_date=schedule_data.departure_date,
            departure_time=schedule_data.departure_time,
            estimated_arrival=schedule_data.estimated_arrival,
            vehicle_id=schedule_data.vehicle_id,
            driver_id=schedule_data.driver_id,
            capacity=vehicle.capacity,
            booked_seats=0,
            available_seats=vehicle.capacity,
            price=schedule_data.price,
            notes=schedule_data.notes,
            created_by=uuid.UUID(user_id)
        )

        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)

        return schedule

    @staticmethod
    async def get_schedule(
        db: AsyncSession,
        schedule_id: str
    ) -> Optional[Schedule]:
        """Get schedule by ID"""
        query = select(Schedule).where(Schedule.id == uuid.UUID(schedule_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_schedules(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get schedules with filters"""
        query = select(Schedule).options(
            selectinload(Schedule.route),
            selectinload(Schedule.vehicle),
            selectinload(Schedule.driver)
        )

        conditions = []

        if filters.get("status"):
            conditions.append(Schedule.status == filters["status"])
        if filters.get("route_id"):
            conditions.append(Schedule.route_id == uuid.UUID(filters["route_id"]))
        if filters.get("departure_date"):
            conditions.append(Schedule.departure_date == filters["departure_date"])
        if filters.get("search"):
            conditions.append(
                or_(
                    Schedule.code.ilike(f"%{filters['search']}%"),
                    Schedule.route.has(
                        Route.origin.ilike(f"%{filters['search']}%")
                    )
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        total_result = await db.execute(
            select(func.count()).select_from(Schedule).where(and_(*conditions))
        )
        total = total_result.scalar()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        query = query.order_by(Schedule.departure_date, Schedule.departure_time)

        result = await db.execute(query)
        schedules = result.scalars().all()

        return {
            "items": schedules,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    @staticmethod
    async def update_schedule(
        db: AsyncSession,
        schedule_id: str,
        schedule_data: ScheduleUpdate,
        user_id: str
    ) -> Optional[Schedule]:
        """Update schedule"""
        schedule = await ScheduleService.get_schedule(db, schedule_id)
        if not schedule:
            return None

        if schedule_data.departure_location:
            schedule.departure_location = schedule_data.departure_location
        if schedule_data.destination:
            schedule.destination = schedule_data.destination
        if schedule_data.departure_date:
            schedule.departure_date = schedule_data.departure_date
        if schedule_data.departure_time:
            schedule.departure_time = schedule_data.departure_time
        if schedule_data.estimated_arrival:
            schedule.estimated_arrival = schedule_data.estimated_arrival
        if schedule_data.vehicle_id:
            # Check vehicle availability
            vehicle = await db.execute(
                select(Vehicle).where(Vehicle.id == schedule_data.vehicle_id)
            )
            vehicle = vehicle.scalar_one_or_none()
            if not vehicle or vehicle.status != VehicleStatus.AVAILABLE:
                raise ValueError("Vehicle not available")
            schedule.vehicle_id = schedule_data.vehicle_id
            schedule.capacity = vehicle.capacity
            schedule.available_seats = vehicle.capacity - schedule.booked_seats
        if schedule_data.driver_id:
            # Check driver availability
            driver = await db.execute(
                select(Driver).where(Driver.id == schedule_data.driver_id)
            )
            driver = driver.scalar_one_or_none()
            if not driver or not driver.is_available:
                raise ValueError("Driver not available")
            schedule.driver_id = schedule_data.driver_id
        if schedule_data.price:
            schedule.price = schedule_data.price
        if schedule_data.notes:
            schedule.notes = schedule_data.notes

        await db.commit()
        await db.refresh(schedule)

        return schedule

    @staticmethod
    async def cancel_schedule(
        db: AsyncSession,
        schedule_id: str,
        reason: str,
        user_id: str
    ) -> Optional[Schedule]:
        """Cancel schedule"""
        schedule = await ScheduleService.get_schedule(db, schedule_id)
        if not schedule:
            return None

        schedule.status = ScheduleStatus.CANCELLED
        schedule.cancelled_at = datetime.utcnow()
        schedule.cancellation_reason = reason

        await db.commit()
        await db.refresh(schedule)

        return schedule