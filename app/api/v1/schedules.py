from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date
import logging

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.services.schedule_service import ScheduleService
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleListResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Create a new schedule"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    try:
        schedule = await ScheduleService.create_schedule(db, schedule_data, str(current_user.id))
        logger.info(f"Schedule created: {schedule.code} by {current_user.email}")
        return schedule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule: {str(e)}"
        )


@router.get("/schedules", response_model=ScheduleListResponse)
async def list_schedules(
    status: Optional[str] = Query(None, description="Filter by status"),
    route_id: Optional[str] = Query(None, description="Filter by route ID"),
    departure_date: Optional[date] = Query(None, description="Filter by departure date"),
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    driver_id: Optional[str] = Query(None, description="Filter by driver ID"),
    search: Optional[str] = Query(None, description="Search by code or location"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """List all schedules with filters"""
    filters = {
        "status": status,
        "route_id": route_id,
        "departure_date": departure_date,
        "vehicle_id": vehicle_id,
        "driver_id": driver_id,
        "search": search,
        "page": page,
        "page_size": page_size
    }

    result = await ScheduleService.get_schedules(db, filters)
    return result


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get schedule by ID"""
    schedule = await ScheduleService.get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return schedule


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    schedule_data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Update schedule"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    schedule = await ScheduleService.update_schedule(db, schedule_id, schedule_data, str(current_user.id))
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return schedule


@router.patch("/schedules/{schedule_id}/cancel")
async def cancel_schedule(
    schedule_id: str,
    reason: str = Query(..., description="Cancellation reason"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Cancel a schedule"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    schedule = await ScheduleService.cancel_schedule(db, schedule_id, reason, str(current_user.id))
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return {"message": f"Schedule {schedule.code} cancelled successfully"}


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Delete schedule (soft delete)"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    deleted = await ScheduleService.delete_schedule(db, schedule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return {"message": "Schedule deleted successfully"}