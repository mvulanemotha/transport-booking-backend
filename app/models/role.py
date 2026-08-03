from sqlalchemy import Column, String, JSON, UUID, Boolean, DateTime, func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import BaseModel


class Role(BaseModel):
    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    permissions = Column(JSON, default={})
    is_system = Column(Boolean, default=False)

    users = relationship("User", back_populates="role")