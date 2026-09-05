# BUSY Class Booking

A deployed studio class-booking system for staff and instructors, covering scheduling, capacity-aware bookings, waitlists, attendance, reporting, immutable booking history and membership expiry alerts.

## Live

- **Application:** https://busy-class-booking.onrender.com
- **API / Swagger:** https://class-booking-system-p6dn.onrender.com/docs
- **Repository:** https://github.com/Shivam29093/class_booking_system

## Stack

- **Frontend:** static HTML, CSS and JavaScript
- **Backend:** FastAPI, SQLAlchemy, Uvicorn
- **Database:** PostgreSQL on Supabase
- **Authentication:** JWT access tokens + bcrypt password hashing
- **Hosting:** Render frontend + Render backend

## Main capabilities

- Staff and instructor roles with server-side authorization
- Class create/edit/archive/restore
- Session scheduling with instructor/room conflict checks
- Primary and co-instructors
- Capacity-aware bookings and waitlists
- Automatic waitlist promotion after cancellation
- Membership expiry enforcement
- Attendance (`ATTENDED` / `NO_SHOW`)
- Server-side booking search/filter/sort/pagination
- Recurring weekly session generation with skipped-conflict reporting
- Attendance CSV export
- Dashboard metrics and eight-week attendance reporting
- Immutable booking history and staff notes
- Membership expiry alerts with dismissal/reappearance behaviour

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system components, deployment and request flow
- [`docs/schema.md`](docs/schema.md) — relational model, relationships and integrity boundaries
- [`docs/plan.md`](docs/plan.md) — build order, time and scope decisions
- [`docs/decisions.md`](docs/decisions.md) — significant architectural/product decisions
- [`docs/ai-prompts.md`](docs/ai-prompts.md) — AI prompts used, corrections and verification
- [`SUBMISSION.md`](SUBMISSION.md) — evaluator-facing links, credentials, checklist and notes

## Validation

The deployed backend was verified with an automated production test flow: **27 passed, 0 failed**. The live frontend was then tested against the deployed API.

Secrets and connection strings are kept in deployment environment variables and are not committed to the repository.
