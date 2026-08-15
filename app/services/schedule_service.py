import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, date, time
import uuid

from app.models.schedule import Schedule, ScheduleStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.driver import Driver, DriverStatus
from app.models.route import Route
from app.schemas.schedule import ScheduleResponse, ScheduleCreate, ScheduleUpdate

from sqlalchemy.orm import selectinload
from sqlalchemy import select

logger = logging.getLogger(__name__)


class ScheduleService:
    @staticmethod
    async def create_schedule(
        db: AsyncSession,
        schedule_data: ScheduleCreate,
        user_id: str
    ) -> Schedule:
        """Create a new schedule"""
        try:
            # Check vehicle availability
            vehicle = await db.execute(
                select(Vehicle).where(Vehicle.id == schedule_data.vehicle_id)
            )
            vehicle = vehicle.scalar_one_or_none()
            if not vehicle or vehicle.status != VehicleStatus.AVAILABLE:
                raise ValueError("Vehicle not available")

            # Check driver availability
            driver = await db.execute(
                select(Driver).where(Driver.id == schedule_data.driver_id)
            )
            driver = driver.scalar_one_or_none()
            if not driver or driver.status != DriverStatus.ACTIVE:
                raise ValueError("Driver not available")

            # Check for conflicts (vehicle or driver already scheduled)
            conflict = await db.execute(
                select(Schedule).where(
                    and_(
                        Schedule.departure_date == schedule_data.departure_date,
                        or_(
                            Schedule.vehicle_id == schedule_data.vehicle_id,
                            Schedule.driver_id == schedule_data.driver_id
                        ),
                        Schedule.status != ScheduleStatus.CANCELLED,
                        Schedule.is_deleted.is_(None)
                    )
                )
            )
            if conflict.scalar_one_or_none():
                raise ValueError("Vehicle or driver already scheduled for this date")

            # Generate schedule code
            today = date.today()
            count = await db.execute(
                select(func.count()).select_from(Schedule)
                .where(Schedule.created_at >= datetime.combine(today, datetime.min.time()))
            )
            count = count.scalar() + 1
            code = f"SCH-{today.strftime('%Y%m%d')}-{str(count).zfill(3)}"

            schedule = Schedule(
                code=code,
                route_id=schedule_data.route_id,
                departure_location=schedule_data.departure_location,
                destination=schedule_data.destination,
                departure_location_detail=schedule_data.departure_location_detail,
                destination_detail=schedule_data.destination_detail,
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

            logger.info(f"✅ Schedule created: {schedule.code}")
            return schedule

        except ValueError as e:
            await db.rollback()
            raise ValueError(str(e))
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error creating schedule: {str(e)}")
            raise Exception(f"Failed to create schedule: {str(e)}")

    @staticmethod
    async def get_schedule(
        db: AsyncSession,
        schedule_id: str
    ) -> Optional[Schedule]:
        """Get schedule by ID"""
        try:
            query = select(Schedule).where(
                and_(
                    Schedule.id == uuid.UUID(schedule_id),
                    Schedule.is_deleted.is_(None)
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting schedule {schedule_id}: {str(e)}")
            return None

    @staticmethod
    async def get_schedules(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get schedules with filters, returning enriched data with route, vehicle, and driver details."""
        try:
            # Base query with eager loading of relationships
            query = select(Schedule).options(
                selectinload(Schedule.route),    # relationship name: 'route'
                selectinload(Schedule.vehicle),  # relationship name: 'vehicle'
                selectinload(Schedule.driver)    # relationship name: 'driver'
            )

            conditions = []

            # Optional: filter out soft-deleted schedules if your model has is_deleted
            # conditions.append(Schedule.is_deleted.is_(None))

            # Apply filters
            if filters.get("status"):
                conditions.append(Schedule.status == filters["status"])
            if filters.get("route_id"):
                conditions.append(Schedule.route_id == uuid.UUID(filters["route_id"]))
            if filters.get("departure_date"):
                conditions.append(Schedule.departure_date == filters["departure_date"])
            if filters.get("vehicle_id"):
                conditions.append(Schedule.vehicle_id == uuid.UUID(filters["vehicle_id"]))
            if filters.get("driver_id"):
                conditions.append(Schedule.driver_id == uuid.UUID(filters["driver_id"]))
            if filters.get("search"):
                search = f"%{filters['search']}%"
                conditions.append(
                    or_(
                        Schedule.code.ilike(search),
                        Schedule.departure_location.ilike(search),
                        Schedule.destination.ilike(search)
                    )
                )

            if conditions:
                query = query.where(and_(*conditions))

            # Count total records (respecting filters)
            count_query = select(func.count()).select_from(Schedule)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Pagination
            page = filters.get("page", 1)
            page_size = filters.get("page_size", 20)
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            query = query.order_by(Schedule.departure_date, Schedule.departure_time)

            result = await db.execute(query)
            schedules = result.scalars().all()

            # Convert each ORM schedule to a Pydantic response model.
            # Because we used selectinload, the nested objects are already loaded.
            items = [
                ScheduleResponse.model_validate(schedule, from_attributes=True)
                for schedule in schedules
            ]

            # Return the paginated response as a dict (or you could return the Pydantic model directly)
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }

        except Exception as e:
            logger.error(f"Error getting schedules: {str(e)}")
            return {"items": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0}

    @staticmethod
    async def update_schedule(
        db: AsyncSession,
        schedule_id: str,
        schedule_data: ScheduleUpdate,
        user_id: str
    ) -> Optional[Schedule]:
        """Update schedule"""
        try:
            schedule = await ScheduleService.get_schedule(db, schedule_id)
            if not schedule:
                return None

            if schedule_data.departure_location is not None:
                schedule.departure_location = schedule_data.departure_location
            if schedule_data.destination is not None:
                schedule.destination = schedule_data.destination
            if schedule_data.departure_location_detail is not None:
                schedule.departure_location_detail = schedule_data.departure_location_detail
            if schedule_data.destination_detail is not None:
                schedule.destination_detail = schedule_data.destination_detail
            if schedule_data.departure_date is not None:
                schedule.departure_date = schedule_data.departure_date
            if schedule_data.departure_time is not None:
                schedule.departure_time = schedule_data.departure_time
            if schedule_data.estimated_arrival is not None:
                schedule.estimated_arrival = schedule_data.estimated_arrival
            if schedule_data.vehicle_id is not None:
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
            if schedule_data.driver_id is not None:
                driver = await db.execute(
                    select(Driver).where(Driver.id == schedule_data.driver_id)
                )
                driver = driver.scalar_one_or_none()
                if not driver or driver.status != DriverStatus.ACTIVE:
                    raise ValueError("Driver not available")
                schedule.driver_id = schedule_data.driver_id
            if schedule_data.price is not None:
                schedule.price = schedule_data.price
            if schedule_data.notes is not None:
                schedule.notes = schedule_data.notes
            if schedule_data.is_holiday is not None:
                schedule.is_holiday = schedule_data.is_holiday
            if schedule_data.is_peak is not None:
                schedule.is_peak = schedule_data.is_peak

            await db.commit()
            await db.refresh(schedule)

            return schedule
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating schedule {schedule_id}: {str(e)}")
            return None

    @staticmethod
    async def cancel_schedule(
        db: AsyncSession,
        schedule_id: str,
        reason: str,
        user_id: str
    ) -> Optional[Schedule]:
        """Cancel schedule"""
        try:
            schedule = await ScheduleService.get_schedule(db, schedule_id)
            if not schedule:
                return None

            schedule.status = ScheduleStatus.CANCELLED
            schedule.cancelled_at = datetime.utcnow()
            schedule.cancellation_reason = reason

            await db.commit()
            await db.refresh(schedule)

            return schedule
        except Exception as e:
            await db.rollback()
            logger.error(f"Error cancelling schedule {schedule_id}: {str(e)}")
            return None

    @staticmethod
    async def delete_schedule(
        db: AsyncSession,
        schedule_id: str
    ) -> bool:
        """Soft delete schedule"""
        try:
            schedule = await ScheduleService.get_schedule(db, schedule_id)
            if not schedule:
                return False

            schedule.is_deleted = datetime.utcnow()
            schedule.status = ScheduleStatus.CANCELLED
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting schedule {schedule_id}: {str(e)}")
            return False