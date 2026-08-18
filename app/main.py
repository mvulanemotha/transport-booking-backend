from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from sqlalchemy import select

from app.models.role import Role
from app.core.database import async_session_maker

from datetime import datetime, timezone

# Use relative imports (without "app.")
from app.api.v1 import auth ,users ,routes , audit ,vehicles , drivers , schedules, customers , bookings, passengers , dashboard , reports  # Import the auth router from the auth.py file
from app.core.config import settings
app = FastAPI(title="Transport Booking System", version="1.0.0")



# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def create_default_roles():
    async with async_session_maker() as session:
        role_names = ["super_admin", "admin", "driver", "customer"]
        for name in role_names:
            exists = await session.execute(select(Role).where(Role.name == name))
            if not exists.scalar_one_or_none():
                now = datetime.now(timezone.utc)
                new_role = Role(
                    name=name,
                    description=f"{name.replace('_', ' ').title()} role",
                    permissions={},
                    is_system=True,
                    is_deleted=False,
                    created_at=now,      # ✅ explicit
                    updated_at=now,      # ✅ explicit
                )
                session.add(new_role)
        await session.commit()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"Validation error on {request.url.path}")
    for error in exc.errors():
        print(f"  - {error['loc']}: {error['msg']} (type: {error['type']})")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# Simple routes
@app.get("/")
async def root():
    return {"message": "Transport Booking System API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/ping")
async def ping():
    return {"message": "pong", "status": "ok"}

# Include auth routes (if auth.py exists with a router)
try:
    #add routes
    app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["auth"])
    app.include_router(users.router , prefix=settings.API_V1_PREFIX, tags=["Users"])
    app.include_router(routes.router, prefix=settings.API_V1_PREFIX, tags=["Routes"])
    app.include_router(vehicles.router, prefix=settings.API_V1_PREFIX, tags=["Vehicles"])
    app.include_router(drivers.router, prefix=settings.API_V1_PREFIX, tags=["Drivers"])
    app.include_router(schedules.router, prefix=settings.API_V1_PREFIX, tags=["Schedules"])
    app.include_router(customers.router, prefix=settings.API_V1_PREFIX, tags=["Customers"])
    app.include_router(bookings.router, prefix=settings.API_V1_PREFIX, tags=["Bookings"])
    app.include_router(passengers.router , prefix=settings.API_V1_PREFIX, tags=["Passangers"])
    app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX, tags=["Dashboard"])
    app.include_router(reports.router, prefix=settings.API_V1_PREFIX, tags=["Reports"])
    app.include_router(reports.router, prefix=settings.API_V1_PREFIX, tags=["Audits"])

    print("✅ Routes loaded")
except Exception as e:
    print(f"⚠️ Auth routes not loaded: {e}")