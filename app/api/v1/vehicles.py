from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.services.vehicle_service import VehicleService
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleListResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/vehicles", response_model=VehicleResponse)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Create a new vehicle"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    try:
        vehicle = await VehicleService.create_vehicle(db, vehicle_data, str(current_user.id))
        logger.info(f"Vehicle created: {vehicle.registration} by {current_user.email}")
        return vehicle
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating vehicle: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vehicle: {str(e)}"
        )


@router.get("/vehicles", response_model=VehicleListResponse)
async def list_vehicles(
    status: Optional[str] = Query(None, description="Filter by status"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    search: Optional[str] = Query(None, description="Search by registration, name, make, model"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """List all vehicles with filters"""
    filters = {
        "status": status,
        "vehicle_type": vehicle_type,
        "search": search,
        "page": page,
        "page_size": page_size
    }

    result = await VehicleService.get_vehicles(db, filters)
    return result


@router.get("/vehicles/available", response_model=list[VehicleResponse])
async def get_available_vehicles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get all available vehicles"""
    vehicles = await VehicleService.get_available_vehicles(db)
    return vehicles


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get vehicle by ID"""
    vehicle = await VehicleService.get_vehicle(db, vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    return vehicle


@router.put("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: str,
    vehicle_data: VehicleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Update vehicle"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    vehicle = await VehicleService.update_vehicle(db, vehicle_id, vehicle_data, str(current_user.id))
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    return vehicle


@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Delete vehicle (soft delete)"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    deleted = await VehicleService.delete_vehicle(db, vehicle_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    return {"message": "Vehicle deleted successfully"}