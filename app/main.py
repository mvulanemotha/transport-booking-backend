from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Use relative imports (without "app.")
from app.api.v1 import auth  # Import the auth router from the auth.py file

app = FastAPI(title="Transport Booking System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#add routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


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
    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    print("✅ Auth routes loaded")
except Exception as e:
    print(f"⚠️ Auth routes not loaded: {e}")