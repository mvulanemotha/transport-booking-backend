import uuid

from fastapi import APIRouter ,Depends , status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi.exceptions import HTTPException

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User

router = APIRouter()


@router.get("/users/me")
async def get_current_user(current_user: User = Depends(SecurityService.get_current_user)):
    """ Get current user information """

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "role": current_user.role.name if current_user.role else None,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "last_login": current_user.last_login,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }

@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """ List all users (Admin only) """

    # Check if user is admin
    if current_user.role.name not in ["super_admin" , "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    result = await db.execute(select(User).options(selectinload(User.role)))
    users = result.scalars().all()

    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.name if u.role else None,
            "is_active": u.is_active
        }
        for u in users
    ]


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    """Get user by ID (Admin only)"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    #query = select(User).where(User.id == uuid.UUID(user_id))
    query = select(User).where(User.id == uuid.UUID(user_id)).options(selectinload(User.role))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role.name if user.role else None,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at
    }