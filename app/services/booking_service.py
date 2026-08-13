import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, date
import uuid

from app.models.booking import Booking, BookingStatus, BookingSource
from app.models.passenger import Passenger
from app.models.schedule import Schedule
from app.models.customer import Customer
from app.schemas.booking import BookingCreate, BookingUpdate

logger = logging.getLogger(__name__)


class BookingService:
    @staticmethod
    async def create_booking(
        db: AsyncSession,
        booking_data: BookingCreate,
        user_id: str
    ) -> Booking:
        """Create a new booking"""
        try:
            # Get schedule and check availability
            schedule = await db.execute(
                select(Schedule).where(Schedule.id == booking_data.schedule_id)
            )
            schedule = schedule.scalar_one_or_none()
            if not schedule:
                raise ValueError("Schedule not found")

            if schedule.available_seats < booking_data.number_of_passengers:
                raise ValueError(f"Only {schedule.available_seats} seats available")

            # Get customer
            customer = await db.execute(
                select(Customer).where(Customer.id == booking_data.customer_id)
            )
            customer = customer.scalar_one_or_none()
            if not customer:
                raise ValueError("Customer not found")

            # Calculate total amount
            total_amount = schedule.price * booking_data.number_of_passengers

            # Generate booking reference
            today = date.today()
            count = await db.execute(
                select(func.count()).select_from(Booking)
                .where(Booking.created_at >= datetime.combine(today, datetime.min.time()))
            )
            count = count.scalar() + 1
            reference = f"MTT-{today.strftime('%Y%m%d')}-{str(count).zfill(6)}"

            # Create booking
            booking = Booking(
                reference=reference,
                customer_id=booking_data.customer_id,
                schedule_id=booking_data.schedule_id,
                vehicle_id=schedule.vehicle_id,
                route_id=schedule.route_id,
                number_of_passengers=booking_data.number_of_passengers,
                total_amount=total_amount,
                paid_amount=0,
                outstanding_balance=total_amount,
                status=BookingStatus.PENDING,
                source=booking_data.source or BookingSource.WEBSITE,
                pickup_location=booking_data.pickup_location,
                dropoff_location=booking_data.dropoff_location,
                notes=booking_data.notes,
                created_by=uuid.UUID(user_id)
            )

            db.add(booking)
            await db.flush()

            # Create passengers
            for passenger_data in booking_data.passengers:
                passenger = Passenger(
                    booking_id=booking.id,
                    full_name=passenger_data.full_name,
                    phone=passenger_data.phone,
                    email=passenger_data.email,
                    id_number=passenger_data.id_number,
                    passport_number=passenger_data.passport_number,
                    nationality=passenger_data.nationality,
                    seat_number=passenger_data.seat_number,
                    pickup_location=passenger_data.pickup_location,
                    dropoff_location=passenger_data.dropoff_location,
                    special_requests=passenger_data.special_requests,
                    emergency_contact=passenger_data.emergency_contact,
                    emergency_phone=passenger_data.emergency_phone,
                    luggage_count=passenger_data.luggage_count,
                    luggage_weight=passenger_data.luggage_weight
                )
                db.add(passenger)

            # Update schedule seats
            schedule.booked_seats += booking_data.number_of_passengers
            schedule.available_seats = schedule.capacity - schedule.booked_seats

            # Update schedule status if fully booked
            if schedule.available_seats == 0:
                schedule.status = "fully_booked"

            await db.commit()
            await db.refresh(booking)

            logger.info(f"✅ Booking created: {booking.reference} - {booking.number_of_passengers} passengers")
            return booking

        except ValueError as e:
            await db.rollback()
            raise ValueError(str(e))
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error creating booking: {str(e)}")
            raise Exception(f"Failed to create booking: {str(e)}")

    @staticmethod
    async def get_booking(
        db: AsyncSession,
        booking_id: str
    ) -> Optional[Booking]:
        """Get booking by ID"""
        try:
            query = select(Booking).where(
                and_(
                    Booking.id == uuid.UUID(booking_id),
                    Booking.is_deleted.is_(None)
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting booking {booking_id}: {str(e)}")
            return None

    @staticmethod
    async def get_booking_by_reference(
        db: AsyncSession,
        reference: str
    ) -> Optional[Booking]:
        """Get booking by reference"""
        try:
            query = select(Booking).where(
                and_(
                    Booking.reference == reference,
                    Booking.is_deleted.is_(None)
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting booking by reference {reference}: {str(e)}")
            return None

    @staticmethod
    async def get_bookings(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get bookings with filters"""
        try:
            query = select(Booking).where(Booking.is_deleted.is_(None))

            conditions = []

            if filters.get("status"):
                conditions.append(Booking.status == filters["status"])
            if filters.get("source"):
                conditions.append(Booking.source == filters["source"])
            if filters.get("customer_id"):
                conditions.append(Booking.customer_id == uuid.UUID(filters["customer_id"]))
            if filters.get("schedule_id"):
                conditions.append(Booking.schedule_id == uuid.UUID(filters["schedule_id"]))
            if filters.get("route_id"):
                conditions.append(Booking.route_id == uuid.UUID(filters["route_id"]))
            if filters.get("date_from"):
                conditions.append(Booking.booking_date >= filters["date_from"])
            if filters.get("date_to"):
                conditions.append(Booking.booking_date <= filters["date_to"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                conditions.append(
                    or_(
                        Booking.reference.ilike(search),
                        Booking.customer.has(Customer.full_name.ilike(search)),
                        Booking.customer.has(Customer.phone.ilike(search))
                    )
                )

            if conditions:
                query = query.where(and_(*conditions))

            total_result = await db.execute(
                select(func.count()).select_from(Booking).where(and_(*conditions) if conditions else Booking.is_deleted.is_(None))
            )
            total = total_result.scalar()

            page = filters.get("page", 1)
            page_size = filters.get("page_size", 20)
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            query = query.order_by(Booking.created_at.desc())

            result = await db.execute(query)
            bookings = result.scalars().all()

            return {
                "items": bookings,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"Error getting bookings: {str(e)}")
            return {"items": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0}

    @staticmethod
    async def update_booking(
        db: AsyncSession,
        booking_id: str,
        booking_data: BookingUpdate,
        user_id: str
    ) -> Optional[Booking]:
        """Update booking"""
        try:
            booking = await BookingService.get_booking(db, booking_id)
            if not booking:
                return None

            if booking_data.status is not None:
                booking.status = booking_data.status
            if booking_data.notes is not None:
                booking.notes = booking_data.notes
            if booking_data.internal_notes is not None:
                booking.internal_notes = booking_data.internal_notes
            if booking_data.pickup_location is not None:
                booking.pickup_location = booking_data.pickup_location
            if booking_data.dropoff_location is not None:
                booking.dropoff_location = booking_data.dropoff_location

            await db.commit()
            await db.refresh(booking)

            return booking
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating booking {booking_id}: {str(e)}")
            return None

    @staticmethod
    async def cancel_booking(
        db: AsyncSession,
        booking_id: str,
        reason: str,
        user_id: str
    ) -> Optional[Booking]:
        """Cancel booking"""
        try:
            booking = await BookingService.get_booking(db, booking_id)
            if not booking:
                return None

            if booking.status in ["completed", "cancelled"]:
                raise ValueError(f"Cannot cancel booking with status: {booking.status}")

            # Update schedule seats
            schedule = await db.execute(
                select(Schedule).where(Schedule.id == booking.schedule_id)
            )
            schedule = schedule.scalar_one_or_none()
            if schedule:
                schedule.booked_seats -= booking.number_of_passengers
                schedule.available_seats = schedule.capacity - schedule.booked_seats
                if schedule.available_seats > 0:
                    schedule.status = "scheduled"

            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = datetime.utcnow()
            booking.cancelled_by = uuid.UUID(user_id)
            booking.cancellation_reason = reason

            await db.commit()
            await db.refresh(booking)

            logger.info(f"✅ Booking cancelled: {booking.reference}")
            return booking
        except Exception as e:
            await db.rollback()
            logger.error(f"Error cancelling booking {booking_id}: {str(e)}")
            return None