import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime
import uuid

from app.models.passenger import Passenger
from app.models.booking import Booking
from app.schemas.passenger import PassengerCreate, PassengerUpdate

logger = logging.getLogger(__name__)


class PassengerService:
    @staticmethod
    async def create_passenger(
        db: AsyncSession,
        passenger_data: PassengerCreate,
        user_id: str
    ) -> Passenger:
        """Create a new passenger"""
        try:
            # Verify booking exists
            booking = await db.execute(
                select(Booking).where(Booking.id == passenger_data.booking_id)
            )
            booking = booking.scalar_one_or_none()
            if not booking:
                raise ValueError("Booking not found")

            passenger = Passenger(
                booking_id=passenger_data.booking_id,
                full_name=passenger_data.full_name,
                phone=passenger_data.phone,
                email=passenger_data.email,
                id_number=passenger_data.id_number,
                passport_number=passenger_data.passport_number,
                nationality=passenger_data.nationality,
                date_of_birth=passenger_data.date_of_birth,
                gender=passenger_data.gender,
                seat_number=passenger_data.seat_number,
                pickup_location=passenger_data.pickup_location,
                dropoff_location=passenger_data.dropoff_location,
                special_requests=passenger_data.special_requests,
                dietary_requirements=passenger_data.dietary_requirements,
                medical_requirements=passenger_data.medical_requirements,
                emergency_contact=passenger_data.emergency_contact,
                emergency_phone=passenger_data.emergency_phone,
                luggage_count=passenger_data.luggage_count,
                luggage_weight=passenger_data.luggage_weight,
            )

            db.add(passenger)
            await db.commit()
            await db.refresh(passenger)

            logger.info(f"✅ Passenger created: {passenger.full_name} for booking {passenger.booking_id}")
            return passenger

        except ValueError as e:
            await db.rollback()
            raise ValueError(str(e))
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error creating passenger: {str(e)}")
            raise Exception(f"Failed to create passenger: {str(e)}")

    @staticmethod
    async def get_passenger(
        db: AsyncSession,
        passenger_id: str
    ) -> Optional[Passenger]:
        """Get passenger by ID"""
        try:
            query = select(Passenger).where(
                and_(
                    Passenger.id == uuid.UUID(passenger_id),
                    Passenger.is_deleted.is_(None)
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting passenger {passenger_id}: {str(e)}")
            return None

    @staticmethod
    async def get_passengers(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get passengers with filters"""
        try:
            query = select(Passenger).where(Passenger.is_deleted.is_(None))

            conditions = []

            if filters.get("booking_id"):
                conditions.append(Passenger.booking_id == uuid.UUID(filters["booking_id"]))
            if filters.get("is_checked_in") is not None:
                conditions.append(Passenger.is_checked_in == filters["is_checked_in"])
            if filters.get("is_boarded") is not None:
                conditions.append(Passenger.is_boarded == filters["is_boarded"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                conditions.append(
                    or_(
                        Passenger.full_name.ilike(search),
                        Passenger.phone.ilike(search),
                        Passenger.email.ilike(search),
                        Passenger.id_number.ilike(search)
                    )
                )

            if conditions:
                query = query.where(and_(*conditions))

            total_result = await db.execute(
                select(func.count()).select_from(Passenger).where(and_(*conditions) if conditions else Passenger.is_deleted.is_(None))
            )
            total = total_result.scalar()

            page = filters.get("page", 1)
            page_size = filters.get("page_size", 20)
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            query = query.order_by(Passenger.full_name)

            result = await db.execute(query)
            passengers = result.scalars().all()

            return {
                "items": passengers,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"Error getting passengers: {str(e)}")
            return {"items": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0}

    @staticmethod
    async def update_passenger(
        db: AsyncSession,
        passenger_id: str,
        passenger_data: PassengerUpdate,
        user_id: str
    ) -> Optional[Passenger]:
        """Update passenger"""
        try:
            passenger = await PassengerService.get_passenger(db, passenger_id)
            if not passenger:
                return None

            if passenger_data.full_name is not None:
                passenger.full_name = passenger_data.full_name
            if passenger_data.phone is not None:
                passenger.phone = passenger_data.phone
            if passenger_data.email is not None:
                passenger.email = passenger_data.email
            if passenger_data.id_number is not None:
                passenger.id_number = passenger_data.id_number
            if passenger_data.passport_number is not None:
                passenger.passport_number = passenger_data.passport_number
            if passenger_data.nationality is not None:
                passenger.nationality = passenger_data.nationality
            if passenger_data.date_of_birth is not None:
                passenger.date_of_birth = passenger_data.date_of_birth
            if passenger_data.gender is not None:
                passenger.gender = passenger_data.gender
            if passenger_data.seat_number is not None:
                passenger.seat_number = passenger_data.seat_number
            if passenger_data.pickup_location is not None:
                passenger.pickup_location = passenger_data.pickup_location
            if passenger_data.dropoff_location is not None:
                passenger.dropoff_location = passenger_data.dropoff_location
            if passenger_data.special_requests is not None:
                passenger.special_requests = passenger_data.special_requests
            if passenger_data.dietary_requirements is not None:
                passenger.dietary_requirements = passenger_data.dietary_requirements
            if passenger_data.medical_requirements is not None:
                passenger.medical_requirements = passenger_data.medical_requirements
            if passenger_data.emergency_contact is not None:
                passenger.emergency_contact = passenger_data.emergency_contact
            if passenger_data.emergency_phone is not None:
                passenger.emergency_phone = passenger_data.emergency_phone
            if passenger_data.luggage_count is not None:
                passenger.luggage_count = passenger_data.luggage_count
            if passenger_data.luggage_weight is not None:
                passenger.luggage_weight = passenger_data.luggage_weight
            if passenger_data.is_checked_in is not None:
                passenger.is_checked_in = passenger_data.is_checked_in
                if passenger_data.is_checked_in:
                    passenger.checked_in_at = datetime.utcnow()
                    passenger.checked_in_by = uuid.UUID(user_id)
            if passenger_data.is_boarded is not None:
                passenger.is_boarded = passenger_data.is_boarded
                if passenger_data.is_boarded:
                    passenger.boarded_at = datetime.utcnow()
                    passenger.boarded_by = uuid.UUID(user_id)

            await db.commit()
            await db.refresh(passenger)

            return passenger
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating passenger {passenger_id}: {str(e)}")
            return None

    @staticmethod
    async def delete_passenger(
        db: AsyncSession,
        passenger_id: str
    ) -> bool:
        """Soft delete passenger"""
        try:
            passenger = await PassengerService.get_passenger(db, passenger_id)
            if not passenger:
                return False

            passenger.is_deleted = datetime.utcnow()
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting passenger {passenger_id}: {str(e)}")
            return False

    @staticmethod
    async def check_in_passenger(
        db: AsyncSession,
        passenger_id: str,
        user_id: str
    ) -> Optional[Passenger]:
        """Check in a passenger"""
        try:
            passenger = await PassengerService.get_passenger(db, passenger_id)
            if not passenger:
                return None

            passenger.is_checked_in = True
            passenger.checked_in_at = datetime.utcnow()
            passenger.checked_in_by = uuid.UUID(user_id)

            await db.commit()
            await db.refresh(passenger)

            logger.info(f"✅ Passenger checked in: {passenger.full_name}")
            return passenger
        except Exception as e:
            await db.rollback()
            logger.error(f"Error checking in passenger {passenger_id}: {str(e)}")
            return None

    @staticmethod
    async def board_passenger(
        db: AsyncSession,
        passenger_id: str,
        user_id: str
    ) -> Optional[Passenger]:
        """Board a passenger"""
        try:
            passenger = await PassengerService.get_passenger(db, passenger_id)
            if not passenger:
                return None

            if not passenger.is_checked_in:
                raise ValueError("Passenger must be checked in before boarding")

            passenger.is_boarded = True
            passenger.boarded_at = datetime.utcnow()
            passenger.boarded_by = uuid.UUID(user_id)

            await db.commit()
            await db.refresh(passenger)

            logger.info(f"✅ Passenger boarded: {passenger.full_name}")
            return passenger
        except Exception as e:
            await db.rollback()
            logger.error(f"Error boarding passenger {passenger_id}: {str(e)}")
            return None