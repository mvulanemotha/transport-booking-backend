from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.security import SecurityService
from app.models.user import User
from app.models.role import Role

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str
    role_name: str = "customer"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login user with email and password"""
    # ✅ Eagerly load the role relationship
    query = select(User).where(User.email == request.email).options(selectinload(User.role))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not SecurityService.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    user.last_login = datetime.utcnow()
    await db.commit()

    # ✅ Now user.role is already loaded, no lazy load needed
    data = {"sub": str(user.id), "email": user.email, "role": user.role.name}

    return TokenResponse(
        access_token=SecurityService.create_access_token(data),
        refresh_token=SecurityService.create_refresh_token(data)
    )


@router.post("/auth/register")
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if email exists
    query = select(User).where(User.email == request.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Check if phone exists
    query = select(User).where(User.phone == request.phone)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone already registered")

    #

    # Get role
    query = select(Role).where(Role.name == request.role_name)
    result = await db.execute(query)
    role = result.scalar_one_or_none()

    if not role:
        # ✅ Auto-create the role with default permissions
        role = Role(name=request.role_name,
                    description=f"Auto-created role: {request.role_name}",
                    permissions={"book_trips": True, "view_bookings": True},
                    is_system=True
                    )
        db.add(role)
        await db.flush()  # Flush to get the role ID

    # ✅ Create user with the role ID
    user = User(
        email=request.email,
        hashed_password=SecurityService.get_password_hash(request.password),
        full_name=request.full_name,
        phone=request.phone,
        role_id=role.id,
        is_active=True
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": role.name,
        "is_active": user.is_active,
        "created_at": user.created_at
    }


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Refresh access token"""
    payload = SecurityService.decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    query = select(User).where(User.id == uuid.UUID(user_id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = {"sub": str(user.id), "email": user.email, "role": user.role.name}

    return TokenResponse(
        access_token=SecurityService.create_access_token(data),
        refresh_token=SecurityService.create_refresh_token(data)
    )