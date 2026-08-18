import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.audit_service import AuditService

router = APIRouter()

def check_admin(current_user: User):
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

@router.get("/users/me")
async def get_current_user(current_user: User = Depends(SecurityService.get_current_user)):
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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    check_admin(current_user)

    query = select(User).options(selectinload(User.role))
    conditions = []
    if search:
        search_term = f"%{search}%"
        conditions.append(
            (User.full_name.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.phone.ilike(search_term))
        )
    if role:
        conditions.append(User.role.has(Role.name == role))
    if is_active is not None:
        conditions.append(User.is_active == is_active)

    if conditions:
        query = query.where(*conditions)

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()

    total_query = select(User).where(*conditions) if conditions else select(User)
    total_result = await db.execute(total_query)
    total = len(total_result.scalars().all())

    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "phone": u.phone,
                "role": u.role.name if u.role else None,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "last_login": u.last_login,
                "created_at": u.created_at,
                "updated_at": u.updated_at
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    check_admin(current_user)
    query = select(User).where(User.id == uuid.UUID(user_id)).options(selectinload(User.role))
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role.name if user.role else None,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "last_login": user.last_login,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    try:
        check_admin(current_user)

        # Check email
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Check phone (if provided)
        if user_data.phone:
            result = await db.execute(select(User).where(User.phone == user_data.phone))
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Phone already registered")

        # Get role
        role_name = user_data.role or "customer"
        result = await db.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=400, detail=f"Role '{role_name}' not found")

        # Hash password
        hashed = SecurityService.get_password_hash(user_data.password)

        new_user = User(
            email=user_data.email,
            hashed_password=hashed,
            full_name=user_data.full_name,
            phone=user_data.phone,
            role_id=role.id,
            is_active=True,
            is_verified=False,
        )
        db.add(new_user)
        await db.flush()

        # Audit log
        await AuditService.audit(
            db,
            user=current_user,
            action="CREATE",
            table_name="users",
            record_id=str(new_user.id),
            changes={
                "email": {"from": None, "to": new_user.email},
                "full_name": {"from": None, "to": new_user.full_name},
                "role": {"from": None, "to": role_name},
            },
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )

        await db.commit()
        await db.refresh(new_user)

        # Reload with role
        result = await db.execute(
            select(User).options(selectinload(User.role)).where(User.id == new_user.id)
        )
        new_user = result.scalar_one()
        return new_user

    except HTTPException:
        raise
    except Exception as e:
        print(f"Create user error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    check_admin(current_user)

    query = select(User).where(User.id == uuid.UUID(user_id)).options(selectinload(User.role))
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = {}
    if user_data.full_name is not None and user_data.full_name != user.full_name:
        changes["full_name"] = {"from": user.full_name, "to": user_data.full_name}
        user.full_name = user_data.full_name
    if user_data.email is not None and user_data.email != user.email:
        existing = await db.execute(select(User).where(User.email == user_data.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already taken")
        changes["email"] = {"from": user.email, "to": user_data.email}
        user.email = user_data.email
    if user_data.phone is not None and user_data.phone != user.phone:
        if user_data.phone:
            existing = await db.execute(select(User).where(User.phone == user_data.phone))
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Phone already taken")
        changes["phone"] = {"from": user.phone, "to": user_data.phone}
        user.phone = user_data.phone
    if user_data.is_active is not None and user_data.is_active != user.is_active:
        changes["is_active"] = {"from": user.is_active, "to": user_data.is_active}
        user.is_active = user_data.is_active
    if user_data.is_verified is not None and user_data.is_verified != user.is_verified:
        changes["is_verified"] = {"from": user.is_verified, "to": user_data.is_verified}
        user.is_verified = user_data.is_verified

    await db.flush()

    if changes:
        await AuditService.audit(
            db,
            user=current_user,
            action="UPDATE",
            table_name="users",
            record_id=str(user.id),
            changes=changes,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )

    await db.commit()
    await db.refresh(user)

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user.id)
    )
    user = result.scalar_one()
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(SecurityService.get_current_user)
):
    check_admin(current_user)

    query = select(User).where(User.id == uuid.UUID(user_id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user.is_active = False
    user.is_deleted = True

    await db.flush()

    await AuditService.audit(
        db,
        user=current_user,
        action="DELETE",
        table_name="users",
        record_id=str(user.id),
        changes={"is_active": {"from": True, "to": False}, "is_deleted": {"from": False, "to": True}},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    await db.commit()
    return {"message": "User deleted successfully"}