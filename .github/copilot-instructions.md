# Project: Assignment 13 — Class Booking

You are working on a Class Booking application based on the assignment README.md in this repository.

IMPORTANT:
- Read README.md completely before making changes.
- Treat README.md as the source of truth for requirements.
- Inspect the existing backend and frontend before writing new code.
- Do NOT rewrite working functionality unnecessarily.
- Preserve the existing architecture and improve it incrementally.
- Reuse existing models, schemas, services, APIs and components where appropriate.
- Every requirement must be enforced on the server, not only hidden in the frontend.
- Do not implement optional stretch features until all 10 required goals are complete.
- Run tests and verify the application after meaningful changes.
- Keep code clean, readable and explainable.
- Do not hardcode secrets, passwords, API keys or database credentials.
- Use environment variables for configuration.
- Make incremental Git commits after meaningful completed features.

## Required goals

1. Accounts and roles
   - Email/password login.
   - At least Studio Staff and Instructor roles.
   - Staff can manage classes, sessions, members and bookings.
   - Instructors can only see/act on sessions where they are primary or co-instructor.
   - Instructors cannot create classes, sessions, members or bookings.
   - Enforce authorization on the backend.

2. Classes
   - Create/edit classes.
   - title, description, discipline, default duration, default capacity.
   - Archive and restore.
   - Archived classes hidden from default views without deleting sessions/bookings.

3. Sessions
   - Belong to exactly one class.
   - date, start time, primary instructor, room, duration, capacity.
   - Duration/capacity default from class but overridable.
   - Staff can create/edit/delete sessions.
   - Opening a class shows its sessions.

4. Booking lifecycle
   - Booking belongs to member + session.
   - If capacity exists => Booked.
   - If full => Waitlisted.
   - Expired membership cannot create a new booking.
   - Booked/Waitlisted can become Cancelled.
   - Cancelling a Booked booking promotes earliest Waitlisted booking.
   - After session time has passed, Booked can become Attended or No Show.
   - Invalid state transitions must be rejected by the server with a useful error.

5. Co-instructors
   - One primary instructor.
   - Multiple co-instructors.
   - Staff can add/remove co-instructors.
   - Instructor can see all sessions where they are primary or co-instructor.

6. Booking search
   - Search by member name/email.
   - Filter by class/session/status.
   - Sort by booked time/status/session.
   - Pagination with total matches.
   - Filtering, sorting and pagination MUST happen server-side.

7. Recurring schedule + attendance CSV
   - Staff can generate sessions over a date range from a weekly recurrence.
   - Report created sessions.
   - Report skipped sessions caused by overlapping instructor/room bookings.
   - Export session attendance as CSV with member and final status.

8. Dashboard
   - Sessions today.
   - Bookings today.
   - No-shows this week.
   - Currently waitlisted members.
   - Booking breakdown by status.
   - Booking breakdown by class.
   - Attendance chart for last eight weeks.

9. Immutable booking history
   - Timeline for every booking.
   - Creation event.
   - Every status change with old/new status and actor.
   - Staff notes.
   - History cannot be edited or deleted.

10. Membership expiry alerts
   - Members expired or expiring within seven days.
   - Alert count badge in navigation.
   - Staff can dismiss alert.
   - If membership is later extended and eventually enters the seven-day window again, alert must return.

## Required documentation

Maintain:

docs/architecture.md
docs/schema.md
docs/plan.md
docs/decisions.md
docs/ai-prompts.md

Update these as development progresses rather than waiting until the end.

## Development strategy

Before changing code:

1. Inspect the repository.
2. Identify what is already implemented.
3. Map existing implementation against the 10 goals.
4. Identify missing functionality.
5. Identify broken functionality.
6. Propose the smallest safe implementation plan.
7. Implement one goal/feature at a time.
8. Test each feature.
9. Do not move to the next major feature until the current one works.

When fixing bugs:
- Find the root cause.
- Make the smallest appropriate fix.
- Do not hide errors.
- Re-run the relevant tests.
- Verify the API manually when useful.

When implementing frontend functionality:
- First inspect the existing API endpoints and schemas.
- Use the existing backend contract rather than inventing a second API.
- Handle loading, error and empty states.
- Respect role-based permissions in the UI while relying on backend authorization for actual security.

When implementing backend functionality:
- Validate business rules on the server.
- Keep business logic in services rather than putting complex logic directly in route handlers where possible.
- Use transactions appropriately for booking/waitlist operations.
- Prevent overbooking and race-condition-prone behavior where practical.

Before considering the project complete:
- Run the full test suite.
- Verify backend startup.
- Verify frontend startup/build.
- Test both Staff and Instructor flows.
- Test the critical booking lifecycle.
- Test invalid authorization attempts.
- Test waitlist promotion.
- Test recurring schedule conflict handling.
- Test CSV export.
- Test dashboard.
- Test immutable history.
- Test membership alerts.
- Verify no secrets are committed.