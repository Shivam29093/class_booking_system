# Plan

## How I split the work

I treated the project as a sequence of vertical slices rather than trying to build the entire UI first:

1. **Foundation:** repository structure, FastAPI application, PostgreSQL/SQLAlchemy setup, models, schemas and authentication.
2. **Core scheduling:** classes, rooms, instructors and sessions, including session conflict checks.
3. **Booking engine:** booking lifecycle, capacity, waitlist, cancellation and automatic promotion.
4. **Operational requirements:** co-instructors, server-side booking search, pagination, attendance and immutable booking history.
5. **Reporting:** recurring session generation, attendance CSV, dashboard metrics and membership expiry alerts.
6. **Frontend:** connect the static frontend to the API and expose the staff workflows.
7. **Validation/deployment:** automated API verification, Supabase configuration, Render backend/frontend deployment, CORS and production end-to-end testing.
8. **Documentation:** architecture, schema, plan, decisions, AI-use record and submission notes.

## Build order and why

I built authentication and the relational model before the UI because nearly every later feature depends on a stable identity and data model. Scheduling came before booking because bookings require real sessions, rooms and instructors. The booking service was then made transactional before adding reporting, so dashboard numbers and history were based on the same business rules as the operational flow.

The frontend was connected after the API was usable. That made it possible to validate the core rules independently with automated requests instead of relying only on browser clicks.

## Estimate vs actual

The original assignment suggested roughly 12 hours. I planned around that size, but the elapsed calendar time was spread across several sessions because deployment and production debugging took longer than the pure implementation work. The largest unexpected work was production integration: database connection setup, Render startup/port behaviour, CORS, and verifying the deployed frontend against the deployed API.

The final verification included an automated production API run with **27 passed and 0 failed** checks, followed by a manual end-to-end browser check of the deployed frontend.

## What I cut when time got tight

I kept the ten required goals as the cutoff and did not spend the remaining time on stretch features. In particular, I did not add payments/package credits, automated reminders, substitute instructors, term-long recurring bookings, public scheduling, payroll, or room-utilization analytics. I also avoided introducing a frontend framework because the static frontend was sufficient for the required workflows and reduced deployment risk.
