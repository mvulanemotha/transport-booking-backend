from pydantic import Field , BaseModel
from typing import Optional, Dict
from datetime import datetime


class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    permissions: Optional[Dict] = {}


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    permissions: Optional[Dict] = None
    is_system: Optional[bool] = None


class RoleResponse(RoleBase):
    id: str
    is_system: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True