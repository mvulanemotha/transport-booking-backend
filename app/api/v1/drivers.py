from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.services.driver_service import DriverService
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse, DriverListResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/drivers", response_model=DriverResponse)
async def create_driver(
    driver_data: DriverCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Create a new driver"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    try:
        driver = await DriverService.create_driver(db, driver_data, str(current_user.id))
        logger.info(f"Driver created: {driver.full_name} by {current_user.email}")
        return driver
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating driver: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create driver: {str(e)}"
        )


@router.get("/drivers", response_model=DriverListResponse)
async def list_drivers(
    status: Optional[str] = Query(None, description="Filter by status"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    search: Optional[str] = Query(None, description="Search by name, phone, license number, email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """List all drivers with filters"""
    filters = {
        "status": status,
        "is_available": is_available,
        "search": search,
        "page": page,
        "page_size": page_size
    }

    result = await DriverService.get_drivers(db, filters)
    return result


@router.get("/drivers/available", response_model=list[DriverResponse])
async def get_available_drivers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get all available drivers"""
    drivers = await DriverService.get_available_drivers(db)
    return drivers


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get driver by ID"""
    driver = await DriverService.get_driver(db, driver_id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    return driver


@router.put("/drivers/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: str,
    driver_data: DriverUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Update driver"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    driver = await DriverService.update_driver(db, driver_id, driver_data, str(current_user.id))
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    return driver


@router.delete("/drivers/{driver_id}")
async def delete_driver(
    driver_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Delete driver (soft delete)"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    deleted = await DriverService.delete_driver(db, driver_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    return {"message": "Driver deleted successfully"}