from sqlalchemy import inspect, text

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
    columns = {column["name"] for column in inspect(engine).get_columns("members")}
    if "expiry_alert_dismissed_for" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE members ADD COLUMN expiry_alert_dismissed_for DATE")
            )
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE booking_history "
                "DROP CONSTRAINT IF EXISTS booking_history_booking_id_fkey"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE booking_history "
                "ADD CONSTRAINT booking_history_booking_id_fkey "
                "FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE RESTRICT"
            )
        )
        connection.execute(
            text(
                "CREATE OR REPLACE FUNCTION prevent_booking_history_mutation() "
                "RETURNS trigger LANGUAGE plpgsql AS $$ "
                "BEGIN RAISE EXCEPTION 'Booking history is immutable'; END; $$"
            )
        )
        connection.execute(
            text(
                "DROP TRIGGER IF EXISTS booking_history_immutable_trigger "
                "ON booking_history"
            )
        )
        connection.execute(
            text(
                "CREATE TRIGGER booking_history_immutable_trigger "
                "BEFORE UPDATE OR DELETE ON booking_history "
                "FOR EACH ROW EXECUTE FUNCTION prevent_booking_history_mutation()"
            )
        )
    print("Database tables created successfully.")


if __name__ == "__main__":
    create_tables()