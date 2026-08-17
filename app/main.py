from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Use relative imports (without "app.")
from app.api.v1 import auth ,users ,routes , vehicles , drivers , schedules, customers , bookings, passengers , dashboard  # Import the auth router from the auth.py file
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


    print("✅ Routes loaded")
except Exception as e:
    print(f"⚠️ Auth routes not loaded: {e}")