from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.services.passenger_service import PassengerService
from app.schemas.passenger import PassengerCreate, PassengerUpdate, PassengerResponse, PassengerListResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/passengers", response_model=PassengerResponse)
async def create_passenger(
    passenger_data: PassengerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Create a new passenger"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    try:
        passenger = await PassengerService.create_passenger(db, passenger_data, str(current_user.id))
        logger.info(f"Passenger created: {passenger.full_name} by {current_user.email}")
        return passenger
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating passenger: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create passenger: {str(e)}"
        )


@router.get("/passengers", response_model=PassengerListResponse)
async def list_passengers(
    booking_id: Optional[str] = Query(None, description="Filter by booking ID"),
    is_checked_in: Optional[bool] = Query(None, description="Filter by check-in status"),
    is_boarded: Optional[bool] = Query(None, description="Filter by boarding status"),
    search: Optional[str] = Query(None, description="Search by name, phone, email, ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """List all passengers with filters"""
    filters = {
        "booking_id": booking_id,
        "is_checked_in": is_checked_in,
        "is_boarded": is_boarded,
        "search": search,
        "page": page,
        "page_size": page_size
    }

    result = await PassengerService.get_passengers(db, filters)
    return result


@router.get("/passengers/{passenger_id}", response_model=PassengerResponse)
async def get_passenger(
    passenger_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get passenger by ID"""
    passenger = await PassengerService.get_passenger(db, passenger_id)
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found"
        )
    return passenger


@router.put("/passengers/{passenger_id}", response_model=PassengerResponse)
async def update_passenger(
    passenger_id: str,
    passenger_data: PassengerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Update passenger"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    passenger = await PassengerService.update_passenger(db, passenger_id, passenger_data, str(current_user.id))
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found"
        )
    return passenger


@router.patch("/passengers/{passenger_id}/check-in")
async def check_in_passenger(
    passenger_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Check in a passenger"""
    if current_user.role.name not in ["super_admin", "admin", "driver"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    passenger = await PassengerService.check_in_passenger(db, passenger_id, str(current_user.id))
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found"
        )
    return {"message": f"Passenger {passenger.full_name} checked in successfully"}


@router.patch("/passengers/{passenger_id}/board")
async def board_passenger(
    passenger_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Board a passenger"""
    if current_user.role.name not in ["super_admin", "admin", "driver"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    passenger = await PassengerService.board_passenger(db, passenger_id, str(current_user.id))
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found"
        )
    return {"message": f"Passenger {passenger.full_name} boarded successfully"}


@router.delete("/passengers/{passenger_id}")
async def delete_passenger(
    passenger_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Delete passenger (soft delete)"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    deleted = await PassengerService.delete_passenger(db, passenger_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found"
        )
    return {"message": "Passenger deleted successfully"}