from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.auth import router as auth_router
from app.core.database import Base, engine
from app.api.classes import router as classes_router
from app.api.members import router as members_router
from app.api.rooms import router as rooms_router
from app.api.instructors import router as instructors_router
from app.api.sessions import router as sessions_router
from app.api.bookings import router as bookings_router
from app.api.reports import router as reports_router
from app.models import (
    Booking,
    BookingHistory,
    ClassModel,
    ClassSession,
    Instructor,
    Member,
    Room,
    User,
)

app = FastAPI(
    title="BUSY Class Booking API",
    description="Class booking and studio management system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://busy-class-booking.onrender.com",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(classes_router)
app.include_router(members_router)
app.include_router(rooms_router)
app.include_router(instructors_router)
app.include_router(sessions_router)
app.include_router(bookings_router)
app.include_router(reports_router)

@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception as e:
        return {
            "status": "error",
            "database": str(e),
        }