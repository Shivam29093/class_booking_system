# Decisions

## Decision 1

- **Chose:** FastAPI + SQLAlchemy + PostgreSQL for the backend.
- **Rejected:** A document database or a backend-only framework with less explicit relational modelling.
- **Why:** The domain is strongly relational: members book sessions, sessions belong to classes and rooms, instructors have primary/co-instructor relationships, and booking history must remain queryable. PostgreSQL and SQLAlchemy make those relationships and constraints explicit.

## Decision 2

- **Chose:** JWT access tokens with bcrypt password hashing and server-side role dependencies.
- **Rejected:** Storing a simple client-side role flag and trusting the browser to hide staff-only actions.
- **Why:** The assignment explicitly requires authorization to be enforced on the server. The browser can improve UX, but it cannot be the security boundary.

## Decision 3

- **Chose:** Store session duration and capacity as concrete session values while using class values as defaults.
- **Rejected:** Reading the class defaults every time a session is displayed or booked.
- **Why:** A session is a scheduled occurrence and may override a class default. Historical sessions should not silently change when the reusable class definition changes.

## Decision 4

- **Chose:** Use a many-to-many `session_instructors` join table for co-instructors, while keeping one explicit primary instructor foreign key on `sessions`.
- **Rejected:** A single comma-separated instructor field or making every instructor assignment indistinguishable.
- **Why:** The requirement distinguishes the primary instructor from additional instructors. The join table represents arbitrary co-instructor membership cleanly and allows an instructor to participate in many sessions.

## Decision 5

- **Chose:** Make booking capacity checks transactional by locking the session row before counting booked records.
- **Rejected:** A simple read-count-write sequence without locking.
- **Why:** Two simultaneous requests could otherwise both see the final available slot and create two bookings. Row locking makes the capacity decision serial for that session.

## Decision 6

- **Chose:** Keep an append-only booking history instead of updating one mutable audit record.
- **Rejected:** A single `last_changed_by`/`last_changed_at` pair on the booking.
- **Why:** The requirement asks for a timeline of every status change and staff note. The history model preserves the sequence and the actor. ORM listeners reject updates/deletes to history rows.

## Decision 7

- **Chose:** Keep the frontend as plain static HTML/CSS/JavaScript.
- **Rejected:** Introducing React/Vite or another frontend build stack.
- **Why:** The assignment allowed any stack and the UI did not need a client-side framework to satisfy the ten goals. A static site was faster to deploy and left the backend as the authoritative business-rule layer.

## Decision 8 — later reversed

- **Chose initially:** Validate the system primarily through manual Swagger/browser testing.
- **Rejected:** Building a dedicated automated production verification script at the beginning.
- **Why initially:** Manual checks were fast while the endpoints were changing rapidly.
- **Later reversed:** Once deployment became the focus, I added an automated `test_api.py` flow because manually repeating authentication, booking, waitlist promotion, history and reporting checks was too error-prone. The production run completed with 27 passed and 0 failed checks.
