from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(200), nullable=True)
    permissions = Column(JSON, nullable=True)          # ✅ JSON, not bool
    is_system = Column(Boolean, default=False)         # ✅ Boolean
    created_at = Column(DateTime(timezone=True), server_default=func.now())   # ✅ DateTime
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())         # ✅ DateTime
    is_deleted = Column(Boolean, default=False)        # ✅ Boolean – NOT DateTime!

    users = relationship("User", back_populates="role")   # ✅ matches User.role