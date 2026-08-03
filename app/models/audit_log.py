from sqlalchemy import Column, String, JSON, UUID, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship
import uuid

from app.core.database import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user_name = Column(String(255))
    user_role = Column(String(50))
    action = Column(String(50), nullable=False)
    table_name = Column(String(100), nullable=False)
    record_id = Column(UUID(as_uuid=True), nullable=False)
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    request_id = Column(String(100))
    changes = Column(JSON)
    reason = Column(String(500))

    user = relationship("User", foreign_keys=[user_id])