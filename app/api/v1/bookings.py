from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.services.booking_service import BookingService
from app.schemas.booking import BookingCreate, BookingUpdate, BookingResponse, BookingListResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/bookings", response_model=BookingResponse)
async def create_booking(
    booking_data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Create a new booking"""
    try:
        booking = await BookingService.create_booking(db, booking_data, str(current_user.id))
        logger.info(f"Booking created: {booking.reference} by {current_user.email}")
        return booking
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create booking: {str(e)}"
        )


@router.get("/bookings", response_model=BookingListResponse)
async def list_bookings(
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    schedule_id: Optional[str] = Query(None, description="Filter by schedule ID"),
    route_id: Optional[str] = Query(None, description="Filter by route ID"),
    date_from: Optional[datetime] = Query(None, description="Filter by start date"),
    date_to: Optional[datetime] = Query(None, description="Filter by end date"),
    search: Optional[str] = Query(None, description="Search by reference or customer name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """List all bookings with filters"""
    filters = {
        "status": status,
        "source": source,
        "customer_id": customer_id,
        "schedule_id": schedule_id,
        "route_id": route_id,
        "date_from": date_from,
        "date_to": date_to,
        "search": search,
        "page": page,
        "page_size": page_size
    }

    result = await BookingService.get_bookings(db, filters)
    return result


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get booking by ID"""
    booking = await BookingService.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    return booking


@router.get("/bookings/reference/{reference}", response_model=BookingResponse)
async def get_booking_by_reference(
    reference: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get booking by reference"""
    booking = await BookingService.get_booking_by_reference(db, reference)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    return booking


@router.put("/bookings/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: str,
    booking_data: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Update booking"""
    booking = await BookingService.update_booking(db, booking_id, booking_data, str(current_user.id))
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    return booking


@router.patch("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    reason: str = Query(..., description="Cancellation reason"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Cancel a booking"""
    try:
        booking = await BookingService.cancel_booking(db, booking_id, reason, str(current_user.id))
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        return {"message": f"Booking {booking.reference} cancelled successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )