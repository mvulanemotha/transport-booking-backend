from sqlalchemy import Column, String, Boolean, ForeignKey, UUID, DateTime, func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)

    role = relationship("Role", back_populates="users")
    customer = relationship(
        "Customer",
        back_populates="user",
        uselist=False,
        foreign_keys="[Customer.user_id]"  # explicitly tells SQLAlchemy to use user_id
    )