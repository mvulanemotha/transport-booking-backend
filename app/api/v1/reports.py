# app/routers/report.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional , List
from datetime import date ,timedelta

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.services.report_service import ReportService
from app.schemas.report import (
    ReportOverview,
    DailyTrend,
    RouteReport,
    PaymentMethodReport,
    VehicleUtilizationReport,
    CustomerGrowthReport,
    RecentBookingReport,
    FullReportResponse
)

router = APIRouter(prefix="/reports", tags=["reports"])

# Common permission check
def check_admin(current_user: User):
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )


@router.get("/overview", response_model=ReportOverview)
async def get_report_overview(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    check_admin(current_user)
    data = await ReportService.get_overview(db, date_from, date_to)
    return data


@router.get("/booking-trends", response_model=List[DailyTrend])
async def get_booking_trends(
    date_from: date = Query(..., description="Start date"),
    date_to: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    check_admin(current_user)
    data = await ReportService.get_booking_trends(db, date_from, date_to)
    return data


@router.get("/route-analysis", response_model=List[RouteReport])
async def get_route_analysis(
    date_from: date = Query(..., description="Start date"),
    date_to: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    check_admin(current_user)
    data = await ReportService.get_route_analysis(db, date_from, date_to)
    return data


@router.get("/payment-methods", response_model=List[PaymentMethodReport])
async def get_payment_methods(
    date_from: date = Query(..., description="Start date"),
    date_to: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    check_admin(current_user)
    data = await ReportService.get_payment_methods(db, date_from, date_to)
    return data


@router.get("/fleet-utilization", response_model=List[VehicleUtilizationReport])
async def get_fleet_utilization(
    date_from: date = Query(..., description="Start date"),
    date_to: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    check_admin(current_user)
    data = await ReportService.get_fleet_utilization(db, date_from, date_to)
    return data


@router.get("/customer-growth", response_model=List[CustomerGrowthReport])
async def get_customer_growth(
    months: int = Query(6, ge=1, le=24, description="Number of months to look back"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    check_admin(current_user)
    data = await ReportService.get_customer_growth(db, months)
    return data


@router.get("/recent-bookings", response_model=List[RecentBookingReport])
async def get_recent_bookings(
    limit: int = Query(5, ge=1, le=50, description="Number of bookings to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    check_admin(current_user)
    data = await ReportService.get_recent_bookings(db, limit)
    return data


@router.get("/full-report", response_model=FullReportResponse)
async def get_full_report(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """
    Fetch all data for the overview tab in one request.
    """
    check_admin(current_user)
    # If no dates, default to last 30 days
    if not date_from:
        date_to = date_to or date.today()
        date_from = date_to - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    overview = await ReportService.get_overview(db, date_from, date_to)
    trends = await ReportService.get_booking_trends(db, date_from, date_to)  # list of DailyTrend
    recent = await ReportService.get_recent_bookings(db, limit=5)

    # ✅ Return the same complete trends for both fields
    return {
        "overview": overview,
        "booking_trends": trends,
        "revenue_trends": trends,
        "recent_bookings": recent
    }


@router.post("/export")
async def export_report(
    report_type: str = Query(..., description="Type of report (bookings, financial, fleet, customer)"),
    format: str = Query(..., description="Export format: pdf, excel, csv"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """
    Export report data in the specified format.
    Currently returns JSON for demonstration; later implement file generation.
    """
    check_admin(current_user)

    # Gather data based on report_type
    data = {}
    if report_type == "bookings":
        data["trends"] = await ReportService.get_booking_trends(db, date_from or date.today() - timedelta(days=30), date_to or date.today())
        data["routes"] = await ReportService.get_route_analysis(db, date_from or date.today() - timedelta(days=30), date_to or date.today())
    elif report_type == "financial":
        data["overview"] = await ReportService.get_overview(db, date_from, date_to)
        data["payment_methods"] = await ReportService.get_payment_methods(db, date_from or date.today() - timedelta(days=30), date_to or date.today())
    elif report_type == "fleet":
        data["utilization"] = await ReportService.get_fleet_utilization(db, date_from or date.today() - timedelta(days=30), date_to or date.today())
    elif report_type == "customer":
        data["growth"] = await ReportService.get_customer_growth(db, 6)
        data["recent"] = await ReportService.get_recent_bookings(db, 10)
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")

    return {
        "message": f"Export requested for {report_type} in {format} format",
        "data": data,
        "format": format,
        "date_range": {"from": date_from, "to": date_to}
    }