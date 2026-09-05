# BUSY Class Booking

BUSY is a studio class-booking application with Staff and Instructor roles,
class/session management, capacity-aware bookings, waitlists, attendance,
recurring schedules, reporting, immutable booking history, and membership
expiry alerts.

## Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Authentication: JWT access tokens and bcrypt password hashing
- Frontend: static HTML, JavaScript, and CSS

## Database Setup

PostgreSQL must be running on port `5432`. Create the application role and
database as a PostgreSQL administrator:

```sql
CREATE USER busy_user WITH PASSWORD 'busy_password';
CREATE DATABASE busy_booking OWNER busy_user;
```

The backend reads connection settings from `backend/.env`. Do not commit that
file or production credentials.

Initialize tables and demo accounts:

```powershell
Push-Location backend
.\venv\Scripts\python.exe create_tables.py
.\venv\Scripts\python.exe seed.py
Pop-Location
```

## Run Locally

Start the backend:

```powershell
Push-Location backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API documentation is available at <http://127.0.0.1:8000/docs>.

Start the static frontend in another terminal:

```powershell
Push-Location frontend
python -m http.server 5173 --bind 127.0.0.1
```

Open <http://127.0.0.1:5173>.

## Demo Accounts

These accounts are created by `backend/seed.py` for local development only:

- Staff: `staff@busy.com` / `Staff@123`
- Instructor: `instructor@busy.com` / `Instructor@123`

Change or remove demo credentials before deploying.

## Tests and Validation

```powershell
Push-Location backend
.\venv\Scripts\python.exe -m pytest tests -q
.\venv\Scripts\python.exe -m compileall -q app tests create_tables.py seed.py
Pop-Location
node --check frontend/app.js
git diff --check
```

The backend exposes health at `/health`, authentication at `/auth/login`, and
role-protected management/reporting endpoints under `/classes`, `/sessions`,
`/bookings`, and `/reports`.

## Requirements Covered

The implementation includes role authorization, class archive/restore,
session scheduling and conflicts, co-instructors, booking and waitlist
lifecycle, server-side booking search and pagination, recurring session
creation, attendance CSV export, dashboard reporting, immutable booking
history and staff notes, and membership expiry alerts with dismissal and
reappearance behavior.

No live deployment URL is configured in this repository.
