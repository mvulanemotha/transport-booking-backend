from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
import uuid

from app.models.vehicle import Vehicle, VehicleStatus, VehicleType
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


class VehicleService:
    @staticmethod
    async def create_vehicle(
        db: AsyncSession,
        vehicle_data: VehicleCreate,
        user_id: str
    ) -> Vehicle:
        """Create a new vehicle"""
        # Check if registration exists
        query = select(Vehicle).where(Vehicle.registration == vehicle_data.registration)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Vehicle registration already exists")

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

        return vehicle

    @staticmethod
    async def get_vehicle(
        db: AsyncSession,
        vehicle_id: str
    ) -> Optional[Vehicle]:
        """Get vehicle by ID"""
        query = select(Vehicle).where(Vehicle.id == uuid.UUID(vehicle_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_vehicles(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get vehicles with filters"""
        query = select(Vehicle)

        conditions = []

        if filters.get("status"):
            conditions.append(Vehicle.status == filters["status"])
        if filters.get("vehicle_type"):
            conditions.append(Vehicle.vehicle_type == filters["vehicle_type"])
        if filters.get("search"):
            conditions.append(
                or_(
                    Vehicle.registration.ilike(f"%{filters['search']}%"),
                    Vehicle.name.ilike(f"%{filters['search']}%")
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        total_result = await db.execute(
            select(func.count()).select_from(Vehicle).where(and_(*conditions))
        )
        total = total_result.scalar()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        vehicles = result.scalars().all()

        return {
            "items": vehicles,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    @staticmethod
    async def update_vehicle(
        db: AsyncSession,
        vehicle_id: str,
        vehicle_data: VehicleUpdate,
        user_id: str
    ) -> Optional[Vehicle]:
        """Update vehicle"""
        vehicle = await VehicleService.get_vehicle(db, vehicle_id)
        if not vehicle:
            return None

        if vehicle_data.name is not None:
            vehicle.name = vehicle_data.name
        if vehicle_data.vehicle_type:
            vehicle.vehicle_type = vehicle_data.vehicle_type
        if vehicle_data.capacity:
            vehicle.capacity = vehicle_data.capacity
        if vehicle_data.color:
            vehicle.color = vehicle_data.color
        if vehicle_data.make:
            vehicle.make = vehicle_data.make
        if vehicle_data.model:
            vehicle.model = vehicle_data.model
        if vehicle_data.year:
            vehicle.year = vehicle_data.year
        if vehicle_data.insurance_provider:
            vehicle.insurance_provider = vehicle_data.insurance_provider
        if vehicle_data.insurance_number:
            vehicle.insurance_number = vehicle_data.insurance_number
        if vehicle_data.insurance_expiry:
            vehicle.insurance_expiry = vehicle_data.insurance_expiry
        if vehicle_data.license_number:
            vehicle.license_number = vehicle_data.license_number
        if vehicle_data.license_expiry:
            vehicle.license_expiry = vehicle_data.license_expiry
        if vehicle_data.roadworthy_certificate:
            vehicle.roadworthy_certificate = vehicle_data.roadworthy_certificate
        if vehicle_data.roadworthy_expiry:
            vehicle.roadworthy_expiry = vehicle_data.roadworthy_expiry
        if vehicle_data.status:
            vehicle.status = vehicle_data.status
        if vehicle_data.fuel_type:
            vehicle.fuel_type = vehicle_data.fuel_type
        if vehicle_data.fuel_efficiency:
            vehicle.fuel_efficiency = vehicle_data.fuel_efficiency
        if vehicle_data.tracking_device_id:
            vehicle.tracking_device_id = vehicle_data.tracking_device_id
        if vehicle_data.gps_enabled is not None:
            vehicle.gps_enabled = vehicle_data.gps_enabled
        if vehicle_data.notes:
            vehicle.notes = vehicle_data.notes

        await db.commit()
        await db.refresh(vehicle)

        return vehicle

    @staticmethod
    async def delete_vehicle(
        db: AsyncSession,
        vehicle_id: str
    ) -> bool:
        """Delete vehicle (soft delete)"""
        vehicle = await VehicleService.get_vehicle(db, vehicle_id)
        if not vehicle:
            return False

        await db.delete(vehicle)
        await db.commit()

        return True

    @staticmethod
    async def get_available_vehicles(
        db: AsyncSession
    ) -> list[Vehicle]:
        """Get all available vehicles"""
        query = select(Vehicle).where(
            and_(
                Vehicle.status == VehicleStatus.AVAILABLE,
                Vehicle.is_deleted.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalars().all()