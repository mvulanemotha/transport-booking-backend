from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, date
import uuid

from app.models.booking import Booking, BookingStatus, BookingSource
from app.models.passenger import Passenger
from app.models.schedule import Schedule
from app.models.customer import Customer
from app.models.payment import Payment
from app.schemas.booking import BookingCreate, BookingUpdate, BookingFilters


class BookingService:
    @staticmethod
    async def create_booking(
        db: AsyncSession,
        booking_data: BookingCreate,
        user_id: str
    ) -> Booking:
        """Create a new booking"""
        # Get schedule and check availability
        query = select(Schedule).where(Schedule.id == booking_data.schedule_id)
        result = await db.execute(query)
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise ValueError("Schedule not found")

        if schedule.available_seats < booking_data.number_of_passengers:
            raise ValueError(f"Only {schedule.available_seats} seats available")

        # Get customer
        query = select(Customer).where(Customer.id == booking_data.customer_id)
        result = await db.execute(query)
        customer = result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        # Calculate total amount
        total_amount = schedule.price * booking_data.number_of_passengers

        # Generate booking reference
        today = date.today()
        count = await db.execute(
            select(func.count()).select_from(Booking)
            .where(Booking.created_at >= today)
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

        return booking

    @staticmethod
    async def get_booking(
        db: AsyncSession,
        booking_id: str
    ) -> Optional[Booking]:
        """Get booking by ID"""
        query = select(Booking).where(Booking.id == uuid.UUID(booking_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_bookings(
        db: AsyncSession,
        filters: BookingFilters
    ) -> Dict[str, Any]:
        """Get bookings with filters"""
        query = select(Booking).options(
            selectinload(Booking.customer),
            selectinload(Booking.schedule),
            selectinload(Booking.passengers)
        )

        conditions = []

        if filters.status:
            conditions.append(Booking.status == filters.status)
        if filters.source:
            conditions.append(Booking.source == filters.source)
        if filters.customer_id:
            conditions.append(Booking.customer_id == uuid.UUID(filters.customer_id))
        if filters.schedule_id:
            conditions.append(Booking.schedule_id == uuid.UUID(filters.schedule_id))
        if filters.date_from:
            conditions.append(Booking.booking_date >= filters.date_from)
        if filters.date_to:
            conditions.append(Booking.booking_date <= filters.date_to)
        if filters.search:
            conditions.append(
                or_(
                    Booking.reference.ilike(f"%{filters.search}%"),
                    Booking.customer.has(
                        Customer.full_name.ilike(f"%{filters.search}%")
                    )
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(Booking)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        page = filters.page or 1
        page_size = filters.page_size or 20
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

    @staticmethod
    async def update_booking(
        db: AsyncSession,
        booking_id: str,
        booking_data: BookingUpdate
    ) -> Optional[Booking]:
        """Update booking"""
        booking = await BookingService.get_booking(db, booking_id)
        if not booking:
            return None

        if booking_data.status:
            booking.status = booking_data.status
        if booking_data.notes:
            booking.notes = booking_data.notes
        if booking_data.pickup_location:
            booking.pickup_location = booking_data.pickup_location
        if booking_data.dropoff_location:
            booking.dropoff_location = booking_data.dropoff_location

        await db.commit()
        await db.refresh(booking)

        return booking

    @staticmethod
    async def cancel_booking(
        db: AsyncSession,
        booking_id: str,
        reason: str,
        user_id: str
    ) -> Optional[Booking]:
        """Cancel booking"""
        booking = await BookingService.get_booking(db, booking_id)
        if not booking:
            return None

        if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
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

        # Update booking
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.cancelled_by = uuid.UUID(user_id)
        booking.cancellation_reason = reason

        await db.commit()
        await db.refresh(booking)

        return booking

    @staticmethod
    async def check_in(
        db: AsyncSession,
        booking_id: str,
        passenger_id: str,
        user_id: str
    ) -> Optional[Passenger]:
        """Check in a passenger"""
        passenger = await db.execute(
            select(Passenger).where(Passenger.id == uuid.UUID(passenger_id))
        )
        passenger = passenger.scalar_one_or_none()

        if not passenger or passenger.booking_id != uuid.UUID(booking_id):
            return None

        passenger.is_checked_in = True
        passenger.checked_in_at = datetime.utcnow()
        passenger.checked_in_by = uuid.UUID(user_id)

        # Update booking status if all passengers checked in
        booking = await BookingService.get_booking(db, booking_id)
        if booking:
            all_checked_in = all(
                p.is_checked_in for p in booking.passengers
            )
            if all_checked_in and booking.status != BookingStatus.CHECKED_IN:
                booking.status = BookingStatus.CHECKED_IN

        await db.commit()
        await db.refresh(passenger)

        return passenger

    @staticmethod
    async def get_next_available(
        db: AsyncSession,
        schedule_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get next available schedule for the same route"""
        schedule = await db.execute(
            select(Schedule).where(Schedule.id == uuid.UUID(schedule_id))
        )
        schedule = schedule.scalar_one_or_none()

        if not schedule:
            return None

        # Find next available schedule on same route
        next_schedule = await db.execute(
            select(Schedule)
            .where(
                Schedule.route_id == schedule.route_id,
                Schedule.departure_date > schedule.departure_date,
                Schedule.available_seats > 0,
                Schedule.status == "scheduled"
            )
            .order_by(Schedule.departure_date, Schedule.departure_time)
            .limit(1)
        )
        next_schedule = next_schedule.scalar_one_or_none()

        return next_schedule