## Architecture

The application is a FastAPI service backed by PostgreSQL and SQLAlchemy. Routes
handle authentication and authorization, while booking state changes live in
`backend/app/services/booking_service.py`. The static frontend in `frontend/`
calls the JSON API and uses the server as the authority for role permissions.

Reporting endpoints provide dashboard aggregates, recurrence generation,
membership alerts, and CSV attendance export. Booking history is append-only at
the API boundary and records the acting user for status changes and notes.
