import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime
import uuid

from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogCreate, AuditLogResponse

logger = logging.getLogger(__name__)


class AuditService:

    # ---------- Core method ----------
    @staticmethod
    async def log_action(
        db: AsyncSession,
        log_data: AuditLogCreate
    ) -> AuditLog:
        """Create a new audit log entry."""
        audit_log = AuditLog(**log_data.model_dump())
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        logger.info(f"Audit log created: {audit_log.action} on {audit_log.table_name}")
        return audit_log

    # ---------- Helper method (the one you'll call) ----------
    @staticmethod
    async def audit(
        db: AsyncSession,
        user: User,
        action: str,
        table_name: str,
        record_id: Optional[str] = None,
        changes: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Helper to log an action with user and request details."""
        log_data = AuditLogCreate(
            user_id=user.id,
            user_name=user.full_name,
            user_role=user.role.name if user.role else None,
            action=action,
            table_name=table_name,
            record_id=record_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return await AuditService.log_action(db, log_data)

    # ---------- Query methods ----------
    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get audit logs with filters."""
        query = select(AuditLog)
        conditions = []

        if filters.get("search"):
            search = f"%{filters['search']}%"
            conditions.append(
                or_(
                    AuditLog.user_name.ilike(search),
                    AuditLog.action.ilike(search),
                    AuditLog.table_name.ilike(search),
                    AuditLog.record_id.ilike(search)
                )
            )
        if filters.get("action"):
            conditions.append(AuditLog.action == filters["action"])
        if filters.get("user_id"):
            conditions.append(AuditLog.user_id == uuid.UUID(filters["user_id"]))
        if filters.get("user_name"):
            conditions.append(AuditLog.user_name.ilike(f"%{filters['user_name']}%"))
        if filters.get("table_name"):
            conditions.append(AuditLog.table_name == filters["table_name"])
        if filters.get("start_date"):
            conditions.append(AuditLog.created_at >= filters["start_date"])
        if filters.get("end_date"):
            conditions.append(AuditLog.created_at <= filters["end_date"])

        if conditions:
            query = query.where(and_(*conditions))

        total_result = await db.execute(
            select(func.count()).select_from(AuditLog).where(and_(*conditions) if conditions else True)
        )
        total = total_result.scalar()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(AuditLog.created_at.desc())

        result = await db.execute(query)
        logs = result.scalars().all()

        return {
            "items": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    @staticmethod
    async def get_audit_log(db: AsyncSession, log_id: str) -> Optional[AuditLog]:
        result = await db.execute(
            select(AuditLog).where(AuditLog.id == uuid.UUID(log_id))
        )
        return result.scalar_one_or_none()