from fastapi import FastAPI
from sqlalchemy import text
from app.api.auth import router as auth_router
from app.core.database import Base, engine
from app.api.classes import router as classes_router
from app.api.members import router as members_router
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

app.include_router(auth_router)
app.include_router(classes_router)
app.include_router(members_router)

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