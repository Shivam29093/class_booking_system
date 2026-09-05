# Submission

## Links

- **GitHub repository:** https://github.com/Shivam29093/class_booking_system
- **Live application:** https://busy-class-booking.onrender.com
- **API / Swagger:** https://class-booking-system-p6dn.onrender.com/docs

## Notes for the reviewer

The application is deployed as a Render Static Site (frontend) and Render Web Service (FastAPI backend), with PostgreSQL hosted on Supabase.

The backend may take time to wake on a free hosting tier after inactivity. If the first request is slow, retry once after the service wakes. The live application is seeded with demo data rather than being an empty shell.

A production API verification script was run against the deployed backend and completed with **27 passed, 0 failed** checks. The deployed frontend was then tested manually end-to-end, including login and dashboard access and the core booking workflow.

## Demo credentials

Use the demo accounts provisioned by the project's seed configuration:

| Role | Email | Password |
|---|---|---|
| Staff | `staff@busy.com` | `Staff@123` |
| Instructor | `instructor@busy.com` | `Instructor@123` |

If the production credentials have been rotated since this file was written, use the current credentials configured in the deployment environment instead of changing the repository to store a new secret.

## Stack

| Layer | What you used | Why |
|---|---|---|
| Frontend | Static HTML, JavaScript, CSS | Simple deployment and enough for the required staff workflows |
| Backend | FastAPI + SQLAlchemy + Uvicorn | Explicit API boundaries, validation, role dependencies and relational ORM support |
| Database | PostgreSQL on Supabase | Relational constraints and transactional booking logic |
| Authentication | JWT + bcrypt | Stateless API authentication with password hashes rather than plaintext credentials |
| Hosting | Render frontend + Render backend; Supabase database | Free-tier deployment with a public frontend and separately deployable API/database |

## Goal checklist

| # | Goal | Status | Notes |
|---|---|---|---|
| 1 | Accounts and roles | Done | Staff/instructor roles, JWT authentication and server-side role dependencies. |
| 2 | Classes | Done | Create/edit/archive/restore classes without deleting their sessions/bookings. |
| 3 | Sessions inside classes | Done | Sessions carry date, time, instructor, room, duration and capacity; class defaults are used when appropriate. |
| 4 | Booking lifecycle with rules | Done | Capacity-aware booking, waitlist, membership expiry validation, cancellation, promotion and attendance states. |
| 5 | Co-instructors | Done | Many-to-many `session_instructors` relationship plus primary instructor. |
| 6 | Finding bookings | Done | Server-side search/filter/sort/pagination rather than browser-side loading/filtering. |
| 7 | Recurring schedule + attendance CSV | Done | Weekly recurring generation reports created/skipped sessions; attendance can be exported as CSV. |
| 8 | Dashboard | Done | Today/week metrics, status/class breakdowns, waitlist information and eight-week attendance data. |
| 9 | Immutable booking history | Done | Status transitions and notes are recorded in a timeline; history updates/deletes are rejected. |
| 10 | Expiring membership alerts | Done | Expired/next-seven-day memberships are surfaced, dismissible, and designed to reappear when a later expiry re-enters the alert window. |

## Validation performed

The deployed backend was exercised with an automated production test flow covering authentication, role information, instructors, rooms, class lifecycle, members, sessions, booking capacity/waitlist behaviour, cancellation/promotion, booking history and staff notes, dashboard/reporting, recurring sessions, and class archive/restore.

**Result: 27 passed, 0 failed.**

The browser frontend was subsequently tested against the live API, including authentication and the core operational workflow.

## How much time did you actually spend?

Approximately 12 hours of focused implementation and verification, spread across multiple working sessions. Additional elapsed time went into deployment setup and production debugging, especially the database connection, Render startup/port behaviour, CORS and final frontend/API integration.

## What would you do next, with another 12 hours?

I would add automated CI checks on every push, stronger automated instructor-authorization coverage, more focused unit tests around booking edge cases and recurring conflicts, and a small set of frontend regression tests. I would also improve production observability and add more database indexes after measuring real query patterns.

## What are you least happy with in this codebase, and why?

The frontend is intentionally lightweight, but that also means some UI state and API handling live in a single static JavaScript surface rather than being split into components/modules. The backend reporting and booking flows could also use a deeper automated test matrix. Given the take-home time budget, I prioritized the ten required behaviours, server-side enforcement, transactional booking logic and deployment over introducing additional framework structure.
