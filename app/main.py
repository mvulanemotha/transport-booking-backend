# Create main.py in the app folder
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Transport Booking System", version="1.0.0")

# getting routes
from app.api.v1 import auth


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1", tags=["auth"])



#
#@app.get("/")
#async def root():
#    return {"message": "Transport Booking System API", "version": "1.0.0"}

#@app.get("/health")
#async def health():
#    return {"status": "healthy", "version": "1.0.0"}
