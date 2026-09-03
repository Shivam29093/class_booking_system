from app.core.database import Base, engine
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


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    create_tables()