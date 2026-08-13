import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime
import uuid

from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.vehicle import VehicleCreate, VehicleUpdate

logger = logging.getLogger(__name__)


class VehicleService:
    @staticmethod
    async def create_vehicle(
        db: AsyncSession,
        vehicle_data: VehicleCreate,
        user_id: str
    ) -> Vehicle:
        """Create a new vehicle"""
        try:
            # Check if registration exists
            query = select(Vehicle).where(Vehicle.registration == vehicle_data.registration)
            result = await db.execute(query)
            if result.scalar_one_or_none():
                raise ValueError(f"Vehicle registration '{vehicle_data.registration}' already exists")

            vehicle = Vehicle(
                registration=vehicle_data.registration,
                name=vehicle_data.name,
                vehicle_type=vehicle_data.vehicle_type,
                capacity=vehicle_data.capacity,
                color=vehicle_data.color,
                make=vehicle_data.make,
                model=vehicle_data.model,
                year=vehicle_data.year,
                insurance_provider=vehicle_data.insurance_provider,
                insurance_number=vehicle_data.insurance_number,
                insurance_expiry=vehicle_data.insurance_expiry,
                license_number=vehicle_data.license_number,
                license_expiry=vehicle_data.license_expiry,
                roadworthy_certificate=vehicle_data.roadworthy_certificate,
                roadworthy_expiry=vehicle_data.roadworthy_expiry,
                status=vehicle_data.status or VehicleStatus.AVAILABLE,
                fuel_type=vehicle_data.fuel_type,
                fuel_efficiency=vehicle_data.fuel_efficiency,
                tracking_device_id=vehicle_data.tracking_device_id,
                gps_enabled=vehicle_data.gps_enabled or False,
                notes=vehicle_data.notes,
                created_by=uuid.UUID(user_id)
            )

            db.add(vehicle)
            await db.commit()
            await db.refresh(vehicle)

            logger.info(f"✅ Vehicle created: {vehicle.registration} - {vehicle.name}")
            return vehicle

        except ValueError as e:
            await db.rollback()
            raise ValueError(str(e))
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error creating vehicle: {str(e)}")
            raise Exception(f"Failed to create vehicle: {str(e)}")

    @staticmethod
    async def get_vehicle(
        db: AsyncSession,
        vehicle_id: str
    ) -> Optional[Vehicle]:
        """Get vehicle by ID"""
        try:
            query = select(Vehicle).where(
                and_(
                    Vehicle.id == uuid.UUID(vehicle_id),
                    Vehicle.is_deleted.is_(None)
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting vehicle {vehicle_id}: {str(e)}")
            return None

    @staticmethod
    async def get_vehicles(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get vehicles with filters"""
        try:
            query = select(Vehicle).where(Vehicle.is_deleted.is_(None))

            conditions = []

            if filters.get("status"):
                conditions.append(Vehicle.status == filters["status"])
            if filters.get("vehicle_type"):
                conditions.append(Vehicle.vehicle_type == filters["vehicle_type"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                conditions.append(
                    or_(
                        Vehicle.registration.ilike(search),
                        Vehicle.name.ilike(search),
                        Vehicle.make.ilike(search),
                        Vehicle.model.ilike(search)
                    )
                )

            if conditions:
                query = query.where(and_(*conditions))

            total_result = await db.execute(
                select(func.count()).select_from(Vehicle).where(and_(*conditions) if conditions else Vehicle.is_deleted.is_(None))
            )
            total = total_result.scalar()

            page = filters.get("page", 1)
            page_size = filters.get("page_size", 20)
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            query = query.order_by(Vehicle.registration)

            result = await db.execute(query)
            vehicles = result.scalars().all()

            return {
                "items": vehicles,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"Error getting vehicles: {str(e)}")
            return {"items": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0}

    @staticmethod
    async def get_available_vehicles(
        db: AsyncSession
    ) -> List[Vehicle]:
        """Get all available vehicles"""
        try:
            query = select(Vehicle).where(
                and_(
                    Vehicle.status == VehicleStatus.AVAILABLE,
                    Vehicle.is_deleted.is_(None)
                )
            ).order_by(Vehicle.registration)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting available vehicles: {str(e)}")
            return []

    @staticmethod
    async def update_vehicle(
        db: AsyncSession,
        vehicle_id: str,
        vehicle_data: VehicleUpdate,
        user_id: str
    ) -> Optional[Vehicle]:
        """Update vehicle"""
        try:
            vehicle = await VehicleService.get_vehicle(db, vehicle_id)
            if not vehicle:
                return None

            if vehicle_data.name is not None:
                vehicle.name = vehicle_data.name
            if vehicle_data.vehicle_type is not None:
                vehicle.vehicle_type = vehicle_data.vehicle_type
            if vehicle_data.capacity is not None:
                vehicle.capacity = vehicle_data.capacity
            if vehicle_data.color is not None:
                vehicle.color = vehicle_data.color
            if vehicle_data.make is not None:
                vehicle.make = vehicle_data.make
            if vehicle_data.model is not None:
                vehicle.model = vehicle_data.model
            if vehicle_data.year is not None:
                vehicle.year = vehicle_data.year
            if vehicle_data.insurance_provider is not None:
                vehicle.insurance_provider = vehicle_data.insurance_provider
            if vehicle_data.insurance_number is not None:
                vehicle.insurance_number = vehicle_data.insurance_number
            if vehicle_data.insurance_expiry is not None:
                vehicle.insurance_expiry = vehicle_data.insurance_expiry
            if vehicle_data.license_number is not None:
                vehicle.license_number = vehicle_data.license_number
            if vehicle_data.license_expiry is not None:
                vehicle.license_expiry = vehicle_data.license_expiry
            if vehicle_data.roadworthy_certificate is not None:
                vehicle.roadworthy_certificate = vehicle_data.roadworthy_certificate
            if vehicle_data.roadworthy_expiry is not None:
                vehicle.roadworthy_expiry = vehicle_data.roadworthy_expiry
            if vehicle_data.status is not None:
                vehicle.status = vehicle_data.status
            if vehicle_data.fuel_type is not None:
                vehicle.fuel_type = vehicle_data.fuel_type
            if vehicle_data.fuel_efficiency is not None:
                vehicle.fuel_efficiency = vehicle_data.fuel_efficiency
            if vehicle_data.tracking_device_id is not None:
                vehicle.tracking_device_id = vehicle_data.tracking_device_id
            if vehicle_data.gps_enabled is not None:
                vehicle.gps_enabled = vehicle_data.gps_enabled
            if vehicle_data.notes is not None:
                vehicle.notes = vehicle_data.notes

            await db.commit()
            await db.refresh(vehicle)

            return vehicle
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating vehicle {vehicle_id}: {str(e)}")
            return None

    @staticmethod
    async def delete_vehicle(
        db: AsyncSession,
        vehicle_id: str
    ) -> bool:
        """Soft delete vehicle"""
        try:
            vehicle = await VehicleService.get_vehicle(db, vehicle_id)
            if not vehicle:
                return False

            vehicle.is_deleted = datetime.utcnow()
            vehicle.status = VehicleStatus.INACTIVE
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting vehicle {vehicle_id}: {str(e)}")
            return False