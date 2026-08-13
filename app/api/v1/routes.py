from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.services.route_service import RouteService
from app.schemas.route import RouteCreate, RouteUpdate, RouteResponse, RouteListResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/routes", response_model=RouteResponse)
async def create_route(
    route_data: RouteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Create a new route"""
    # Only super_admin and admin can create routes
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    try:
        route = await RouteService.create_route(db, route_data, str(current_user.id))
        logger.info(f"Route created: {route.code} by {current_user.email}")
        return route
    except ValueError as e:
        logger.error(f"Value error creating route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create route: {str(e)}"
        )


@router.get("/routes", response_model=RouteListResponse)
async def list_routes(
    search: Optional[str] = Query(None, description="Search by code, name, origin, destination"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_international: Optional[bool] = Query(None, description="Filter by international status"),
    origin: Optional[str] = Query(None, description="Filter by origin"),
    destination: Optional[str] = Query(None, description="Filter by destination"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """List all routes with filters"""
    filters = {
        "search": search,
        "is_active": is_active,
        "is_international": is_international,
        "origin": origin,
        "destination": destination,
        "page": page,
        "page_size": page_size
    }

    result = await RouteService.get_routes(db, filters)
    return result


@router.get("/routes/active", response_model=list[RouteResponse])
async def get_active_routes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get all active routes"""
    routes = await RouteService.get_active_routes(db)
    return routes


@router.get("/routes/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get route by ID"""
    route = await RouteService.get_route(db, route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    return route


@router.put("/routes/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: str,
    route_data: RouteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Update route"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    route = await RouteService.update_route(db, route_id, route_data, str(current_user.id))
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    return route


@router.delete("/routes/{route_id}")
async def delete_route(
    route_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Delete route (soft delete)"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    try:
        deleted = await RouteService.delete_route(db, route_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        return {"message": "Route deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete route: {str(e)}"
        )