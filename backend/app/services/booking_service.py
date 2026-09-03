from datetime import date, datetime

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

    # A member can have only one booking per session.
    existing_booking = (
        db.query(Booking)
        .filter(
            Booking.session_id == session_id,
            Booking.member_id == member_id,
        )
        .first()
    )

    if existing_booking:
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

    # Lock the booking while changing its status.
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