from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
import uuid

from app.models.driver import Driver, DriverStatus
from app.models.user import User
from app.schemas.driver import DriverCreate, DriverUpdate


class DriverService:
    @staticmethod
    async def create_driver(
        db: AsyncSession,
        driver_data: DriverCreate,
        user_id: str
    ) -> Driver:
        """Create a new driver"""
        # Check if license number exists
        query = select(Driver).where(Driver.license_number == driver_data.license_number)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Driver license number already exists")

        # Check if phone exists
        query = select(Driver).where(Driver.phone == driver_data.phone)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Phone number already registered")

        driver = Driver(
            full_name=driver_data.full_name,
            phone=driver_data.phone,
            email=driver_data.email,
            license_number=driver_data.license_number,
            license_class=driver_data.license_class,
            license_expiry=driver_data.license_expiry,
            status=driver_data.status or DriverStatus.ACTIVE,
            notes=driver_data.notes,
            created_by=uuid.UUID(user_id)
        )

        db.add(driver)
        await db.commit()
        await db.refresh(driver)

        return driver

    @staticmethod
    async def get_driver(
        db: AsyncSession,
        driver_id: str
    ) -> Optional[Driver]:
        """Get driver by ID"""
        query = select(Driver).where(Driver.id == uuid.UUID(driver_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_drivers(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get drivers with filters"""
        query = select(Driver)

        conditions = []

        if filters.get("status"):
            conditions.append(Driver.status == filters["status"])
        if filters.get("is_available") is not None:
            conditions.append(Driver.is_available == filters["is_available"])
        if filters.get("search"):
            conditions.append(
                or_(
                    Driver.full_name.ilike(f"%{filters['search']}%"),
                    Driver.phone.ilike(f"%{filters['search']}%"),
                    Driver.license_number.ilike(f"%{filters['search']}%")
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        total_result = await db.execute(
            select(func.count()).select_from(Driver).where(and_(*conditions))
        )
        total = total_result.scalar()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        drivers = result.scalars().all()

        return {
            "items": drivers,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    @staticmethod
    async def update_driver(
        db: AsyncSession,
        driver_id: str,
        driver_data: DriverUpdate,
        user_id: str
    ) -> Optional[Driver]:
        """Update driver"""
        driver = await DriverService.get_driver(db, driver_id)
        if not driver:
            return None

        if driver_data.full_name:
            driver.full_name = driver_data.full_name
        if driver_data.phone:
            driver.phone = driver_data.phone
        if driver_data.email:
            driver.email = driver_data.email
        if driver_data.license_number:
            driver.license_number = driver_data.license_number
        if driver_data.license_class:
            driver.license_class = driver_data.license_class
        if driver_data.license_expiry:
            driver.license_expiry = driver_data.license_expiry
        if driver_data.status:
            driver.status = driver_data.status
        if driver_data.is_available is not None:
            driver.is_available = driver_data.is_available
        if driver_data.notes:
            driver.notes = driver_data.notes

        await db.commit()
        await db.refresh(driver)

        return driver

    @staticmethod
    async def delete_driver(
        db: AsyncSession,
        driver_id: str
    ) -> bool:
        """Delete driver"""
        driver = await DriverService.get_driver(db, driver_id)
        if not driver:
            return False

        await db.delete(driver)
        await db.commit()

        return True

    @staticmethod
    async def get_available_drivers(
        db: AsyncSession
    ) -> list[Driver]:
        """Get all available drivers"""
        query = select(Driver).where(
            and_(
                Driver.is_available == True,
                Driver.status == DriverStatus.ACTIVE
            )
        )
        result = await db.execute(query)
        return result.scalars().all()