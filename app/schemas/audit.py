from pydantic import BaseModel, UUID4
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLogBase(BaseModel):
    user_id: Optional[UUID4] = None
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    action: str
    table_name: str
    record_id: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int