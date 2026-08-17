# app/routers/dashboard.py
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import KPIData

from app.schemas.dashboard import DashboardChartsData

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpi", response_model=KPIData)
async def get_dashboard_kpi(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user),
):
    """Get KPI data for the admin dashboard."""
    # Only allow admin and super_admin roles
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    data = await DashboardService.get_kpi_data(db)
    return data


@router.get("/charts", response_model=DashboardChartsData)
async def get_dashboard_charts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get all chart data for the dashboard (trends, routes, utilization, activity)."""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    booking_trends = await DashboardService.get_booking_trends(db)
    revenue_trends = await DashboardService.get_revenue_trends(db)
    popular_routes = await DashboardService.get_popular_routes(db)
    utilization = await DashboardService.get_vehicle_utilization(db)
    recent_activity = await DashboardService.get_recent_activity(db)

    return DashboardChartsData(
        booking_trends=booking_trends,
        revenue_trends=revenue_trends,
        popular_routes=popular_routes,
        utilization=utilization,
        recent_activity=recent_activity
    )