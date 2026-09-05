# Architecture

## Moving pieces

The application is split into three deployed pieces:

- **Browser frontend:** static HTML, CSS and JavaScript. It is served as a Render Static Site at `https://busy-class-booking.onrender.com` and calls the backend over HTTPS.
- **API backend:** FastAPI running with Uvicorn. It is deployed as a Render Web Service at `https://class-booking-system-p6dn.onrender.com`. The backend owns authentication, authorization, business rules, reporting and database access.
- **Database:** PostgreSQL hosted by Supabase. SQLAlchemy is used as the ORM and the backend reads the database connection string from environment configuration rather than from source control.

Authentication uses JWT access tokens and bcrypt password hashing. The backend exposes OpenAPI/Swagger documentation at `/docs`.

## Where each piece runs

| Piece | Runtime / host | Responsibility |
|---|---|---|
| Frontend | Render Static Site | UI, navigation, API calls, rendering results |
| Backend | Render Web Service / FastAPI + Uvicorn | REST API, role checks, business logic |
| Database | Supabase PostgreSQL | Persistent relational data |

The public frontend is the primary entry point. The API is independently reachable for inspection through Swagger.

## Representative request path: creating a booking

1. A staff user signs in through the browser.
2. The frontend sends the email/password to `POST /auth/login`.
3. FastAPI validates the credentials and returns a JWT access token.
4. The browser keeps the token and sends it with authenticated API requests.
5. The staff UI submits a booking request to the bookings API with a member and session.
6. The server authenticates the JWT and enforces the staff role before reaching the booking service.
7. The booking service loads the session and locks its row with `SELECT ... FOR UPDATE`. This prevents concurrent requests from exceeding capacity.
8. The service checks membership expiry, duplicate booking state, session start time and current booked count.
9. The booking is stored as `BOOKED` when capacity exists, otherwise `WAITLISTED`.
10. A `BookingHistory` record is written for the event in the same transaction.
11. PostgreSQL commits the changes.
12. FastAPI returns the booking state and the frontend refreshes its view.

Cancellation follows the same path, but when a booked slot is freed the service locks and promotes the earliest waitlisted booking, recording the promotion in immutable history.

## What I deliberately did not build

The required ten goals were the cutoff. I did not build the optional stretch features such as paid/package membership billing, automated reminder messaging, substitute-instructor workflows, term-long recurring bookings, public class scheduling, payroll, or room-utilization analytics. Those would add product surface area without improving the required booking workflow enough for this take-home.

I also kept the frontend as a static JavaScript application rather than introducing a heavier frontend framework. The assignment did not require a particular UI stack, and the static approach reduced build/deployment complexity while leaving the API as the clear boundary for business rules.
