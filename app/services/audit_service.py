from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime
import uuid

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: Optional[uuid.UUID],
        action: str,
        table_name: str,
        record_id: uuid.UUID,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> AuditLog:
        """Log an action to the audit trail"""
        user_name = None
        user_role = None

        if user_id:
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            if user:
                user_name = user.full_name
                user_role = user.role.name if user.role else None

        # Calculate changes summary
        changes = None
        if old_values and new_values:
            changes = {}
            for key in new_values:
                if key in old_values and old_values[key] != new_values[key]:
                    changes[key] = {
                        "from": old_values[key],
                        "to": new_values[key]
                    }

        audit_log = AuditLog(
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            changes=changes,
            reason=reason
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        return audit_log

    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get audit logs with filters"""
        query = select(AuditLog)

        conditions = []

        if filters.get("user_id"):
            conditions.append(AuditLog.user_id == uuid.UUID(filters["user_id"]))
        if filters.get("action"):
            conditions.append(AuditLog.action == filters["action"])
        if filters.get("table_name"):
            conditions.append(AuditLog.table_name == filters["table_name"])
        if filters.get("record_id"):
            conditions.append(AuditLog.record_id == uuid.UUID(filters["record_id"]))
        if filters.get("start_date"):
            conditions.append(AuditLog.created_at >= filters["start_date"])
        if filters.get("end_date"):
            conditions.append(AuditLog.created_at <= filters["end_date"])
        if filters.get("search"):
            search = f"%{filters['search']}%"
            conditions.append(
                or_(
                    AuditLog.user_name.ilike(search),
                    AuditLog.action.ilike(search),
                    AuditLog.table_name.ilike(search)
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        total_result = await db.execute(
            select(func.count()).select_from(AuditLog).where(and_(*conditions))
        )
        total = total_result.scalar()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 50)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        query = query.order_by(AuditLog.created_at.desc())

        result = await db.execute(query)
        logs = result.scalars().all()

        return {
            "items": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }