# Schema

## Overview

The database uses PostgreSQL and is designed around the main studio entities:
users, members, instructors, classes, rooms, sessions, bookings and immutable
booking history.

The schema is mostly normalized. Many-to-many relationships are represented
using explicit junction tables.

## Tables

### users

Stores login credentials and application roles.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| email | VARCHAR | Unique, required |
| password_hash | VARCHAR | Required |
| role | VARCHAR | STAFF or INSTRUCTOR |
| created_at | TIMESTAMP | Required |

### members

Stores members who can book sessions.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR | Required |
| email | VARCHAR | Required |
| membership_expiry | DATE | Required |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### instructors

Stores instructor-specific information linked to a user account.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| name | VARCHAR | Required |

### classes

Stores reusable class definitions.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| title | VARCHAR | Required |
| description | TEXT | Required |
| discipline | VARCHAR | Required |
| default_duration_minutes | INTEGER | Required |
| default_capacity | INTEGER | Required |
| is_archived | BOOLEAN | Default false |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### rooms

Stores studio rooms.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR | Unique, required |

### sessions

Stores scheduled occurrences of a class.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| class_id | UUID | Foreign key to classes |
| session_date | DATE | Required |
| start_time | TIME | Required |
| primary_instructor_id | UUID | Foreign key to instructors |
| room_id | UUID | Foreign key to rooms |
| duration_minutes | INTEGER | Required |
| capacity | INTEGER | Required |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### session_instructors

Junction table for session co-instructors.

| Column | Type | Notes |
|---|---|---|
| session_id | UUID | Foreign key to sessions |
| instructor_id | UUID | Foreign key to instructors |

Primary key: `(session_id, instructor_id)`.

### bookings

Stores a member's booking for a session.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| session_id | UUID | Foreign key to sessions |
| member_id | UUID | Foreign key to members |
| status | VARCHAR | Booking lifecycle state |
| booked_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### booking_history

Append-only record of booking creation and status changes.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| booking_id | UUID | Foreign key to bookings |
| event_type | VARCHAR | Required |
| old_status | VARCHAR | Nullable |
| new_status | VARCHAR | Nullable |
| note | TEXT | Nullable |
| changed_by_user_id | UUID | Foreign key to users |
| created_at | TIMESTAMP | Required |

## Relationships

- One class has many sessions.
- One room has many sessions.
- One instructor can be the primary instructor for many sessions.
- Sessions and instructors have a many-to-many relationship through `session_instructors`.
- One session has many bookings.
- One member can have many bookings.
- One booking has many immutable history records.
- One user can create many booking-history records.
- An instructor is linked to one user account.

## Database vs application constraints

Database constraints will enforce identity and structural integrity such as:

- Primary keys
- Foreign keys
- Unique email addresses
- Unique room names
- Unique `(session_id, instructor_id)`
- Unique `(session_id, member_id)` for a member's booking

Application/service logic will enforce business rules such as:

- Membership expiry
- Booking capacity
- Valid booking status transitions
- Waitlist promotion
- Instructor authorization
- Session time restrictions
- Recurring-session conflict detection

## Denormalisation

No deliberate denormalisation is planned initially.

Session capacity and duration are stored directly on each session rather than
looked up from the class at booking time because they can be overridden per
session.

## Scaling considerations

At 100x the current data volume, booking and dashboard queries would be the
first areas requiring attention. Indexes on session dates, booking status,
member/session foreign keys and booking timestamps would become increasingly
important. Dashboard aggregation may eventually need precomputed summaries or
caching.