from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.booking_history import BookingHistory
from app.models.enums import BookingEventType, BookingStatus
from app.models.member import Member
from app.models.session import ClassSession

def add_history(
    db: Session,
    booking: Booking,
    event_type: BookingEventType,
    old_status: BookingStatus | None,
    new_status: BookingStatus | None,
    user_id,
    note: str | None = None,
):
    history = BookingHistory(
        booking_id=booking.id,
        event_type=event_type,
        old_status=old_status,
        new_status=new_status,
        changed_by_user_id=user_id,
        note=note,
    )

    db.add(history)


def booking_event_for_status(status: BookingStatus) -> BookingEventType:
    if status == BookingStatus.BOOKED:
        return BookingEventType.CONFIRMED
    if status == BookingStatus.WAITLISTED:
        return BookingEventType.WAITLISTED
    raise ValueError(f"Unsupported booking status: {status}")


def create_booking(
    db: Session,
    session_id,
    member_id,
    user_id,
) -> Booking:

    # Lock the session row so simultaneous bookings cannot
    # exceed the session capacity.
    session = (
        db.query(ClassSession)
        .filter(ClassSession.id == session_id)
        .with_for_update()
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    member = (
        db.query(Member)
        .filter(Member.id == member_id)
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found",
        )

    # Membership is valid through the expiry date.
    if member.membership_expiry < date.today():
        raise HTTPException(
            status_code=400,
            detail="Member membership has expired",
        )

    # A member can have only one booking record per session.
    # We check ALL statuses because the database has a unique
    # constraint on (session_id, member_id).
    existing_booking = (
        db.query(Booking)
        .filter(
            Booking.session_id == session_id,
            Booking.member_id == member_id,
        )
        .first()
    )

    # Already booked or waitlisted.
    if existing_booking and existing_booking.status in (
        BookingStatus.BOOKED,
        BookingStatus.WAITLISTED,
    ):
        raise HTTPException(
            status_code=409,
            detail="Member already has a booking for this session",
        )

    # Do not allow new bookings after the session has started.
    session_start = datetime.combine(
        session.session_date,
        session.start_time,
    )

    if datetime.now() >= session_start:
        raise HTTPException(
            status_code=400,
            detail="Cannot create a booking after the session has started",
        )

    # Count only currently BOOKED members.
    booked_count = (
        db.query(Booking)
        .filter(
            Booking.session_id == session.id,
            Booking.status == BookingStatus.BOOKED,
        )
        .count()
    )

    if booked_count < session.capacity:
        booking_status = BookingStatus.BOOKED
    else:
        booking_status = BookingStatus.WAITLISTED

    # If a previous booking was cancelled, reuse that row
    # instead of creating a duplicate row.
    if existing_booking:
        old_status = existing_booking.status

        existing_booking.status = booking_status
        existing_booking.booked_at = datetime.now()
        existing_booking.updated_at = datetime.now()

        add_history(
            db=db,
            booking=existing_booking,
            event_type=booking_event_for_status(booking_status),
            old_status=old_status,
            new_status=booking_status,
            user_id=user_id,
            note="Booking reactivated",
        )

        db.commit()
        db.refresh(existing_booking)

        return existing_booking

    # No previous booking exists, so create a new one.
    booking = Booking(
        session_id=session.id,
        member_id=member.id,
        status=booking_status,
    )

    db.add(booking)
    db.flush()

    add_history(
        db=db,
        booking=booking,
        event_type=BookingEventType.CREATED,
        old_status=None,
        new_status=booking_status,
        user_id=user_id,
        note="Booking created",
    )

    db.commit()
    db.refresh(booking)

    return booking

def cancel_booking(
    db: Session,
    booking_id,
    user_id,
) -> Booking:

    # Lock the session first, matching create_booking's lock order.
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    session = (
        db.query(ClassSession)
        .filter(ClassSession.id == booking.session_id)
        .with_for_update()
        .first()
    )
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .with_for_update()
        .first()
    )

    if booking.status not in {
        BookingStatus.BOOKED,
        BookingStatus.WAITLISTED,
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot cancel booking with status "
                f"{booking.status}"
            ),
        )

    old_status = booking.status

    booking.status = BookingStatus.CANCELLED

    add_history(
        db=db,
        booking=booking,
        event_type=BookingEventType.CANCELLED,
        old_status=old_status,
        new_status=BookingStatus.CANCELLED,
        user_id=user_id,
        note="Booking cancelled",
    )

    # If a BOOKED slot was freed, promote the earliest waitlisted member.
    if old_status == BookingStatus.BOOKED:

        next_waitlisted = (
            db.query(Booking)
            .filter(
                Booking.session_id == booking.session_id,
                Booking.status == BookingStatus.WAITLISTED,
            )
            .order_by(
                Booking.booked_at.asc(),
                Booking.id.asc(),
            )
            .with_for_update()
            .first()
        )

        if next_waitlisted:
            next_waitlisted.status = BookingStatus.BOOKED
            next_waitlisted.updated_at = datetime.now()

            add_history(
                db=db,
                booking=next_waitlisted,
                event_type=BookingEventType.PROMOTED,
                old_status=BookingStatus.WAITLISTED,
                new_status=BookingStatus.BOOKED,
                user_id=user_id,
                note="Automatically promoted from waitlist",
            )

    db.commit()
    db.refresh(booking)

    return booking
def mark_attendance(
    db: Session,
    booking_id,
    attendance_status: BookingStatus,
    user_id,
) -> Booking:

    # Lock the booking while changing attendance.
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .with_for_update()
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    # Only BOOKED members can have attendance recorded.
    if booking.status != BookingStatus.BOOKED:
        raise HTTPException(
            status_code=400,
            detail=(
                "Attendance can only be marked for a BOOKED booking"
            ),
        )

    # Only ATTENDED or NO_SHOW are valid attendance states.
    if attendance_status not in {
        BookingStatus.ATTENDED,
        BookingStatus.NO_SHOW,
    }:
        raise HTTPException(
            status_code=400,
            detail="Attendance status must be ATTENDED or NO_SHOW",
        )

    session = (
        db.query(ClassSession)
        .filter(ClassSession.id == booking.session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    session_end = datetime.combine(
        session.session_date,
        session.start_time,
    ) + timedelta(minutes=session.duration_minutes)

    if datetime.now() < session_end:
        raise HTTPException(
            status_code=400,
            detail="Cannot mark attendance before the session has ended",
        )

    old_status = booking.status

    booking.status = attendance_status
    booking.updated_at = datetime.now()

    add_history(
        db=db,
        booking=booking,
        event_type=BookingEventType.ATTENDANCE_MARKED,
        old_status=old_status,
        new_status=attendance_status,
        user_id=user_id,
        note=f"Attendance marked as {attendance_status.value}",
    )

    db.commit()
    db.refresh(booking)

    return booking