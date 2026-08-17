from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.services.audit_service import AuditService
from app.schemas.audit import AuditLogResponse, AuditLogListResponse

router = APIRouter(prefix="/audit", tags=["audit"])


def check_admin(current_user: User):
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )


@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    search: Optional[str] = Query(None, description="Search by user, action, table, record"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    user_name: Optional[str] = Query(None, description="Filter by user name"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get audit logs with filters (admin only)."""
    check_admin(current_user)

    filters = {
        "search": search,
        "action": action,
        "user_id": user_id,
        "user_name": user_name,
        "table_name": table_name,
        "start_date": start_date,
        "end_date": end_date,
        "page": page,
        "page_size": page_size,
    }
    result = await AuditService.get_audit_logs(db, filters)
    return result


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get a single audit log by ID."""
    check_admin(current_user)
    log = await AuditService.get_audit_log(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    return log


@router.post("/export")
async def export_audit_logs(
    search: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Export audit logs (CSV or JSON). For now returns JSON."""
    check_admin(current_user)
    filters = {
        "search": search,
        "action": action,
        "user_id": user_id,
        "start_date": start_date,
        "end_date": end_date,
        "page": 1,
        "page_size": 1000,  # max for export
    }
    result = await AuditService.get_audit_logs(db, filters)
    # In real implementation, generate CSV/PDF and return file
    return {
        "message": "Export successful",
        "data": result["items"],
        "total": result["total"]
    }