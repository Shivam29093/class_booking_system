from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.booking_history import BookingHistory
from app.api.dependencies import require_staff
from app.core.database import get_db
from app.models.booking import Booking
from app.models.user import User
from app.schemas.booking import (
    AttendanceUpdate,
    BookingCreate,
    BookingResponse,
    BookingHistoryResponse,
)
from app.services.booking_service import (
    cancel_booking,
    create_booking,
    mark_attendance,
)

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)


@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_booking_endpoint(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return create_booking(
        db=db,
        session_id=payload.session_id,
        member_id=payload.member_id,
        user_id=current_user.id,
    )


@router.get(
    "",
    response_model=list[BookingResponse],
)
def list_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return (
        db.query(Booking)
        .order_by(Booking.booked_at.desc())
        .all()
    )


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
)
def get_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    return booking


@router.get(
    "/{booking_id}/history",
    response_model=list[BookingHistoryResponse],
)
def get_booking_history(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    return (
        db.query(BookingHistory)
        .filter(BookingHistory.booking_id == booking_id)
        .order_by(BookingHistory.created_at.asc())
        .all()
    )
@router.post(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
)
def cancel_booking_endpoint(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return cancel_booking(
        db=db,
        booking_id=booking_id,
        user_id=current_user.id,
    )


@router.post(
    "/{booking_id}/attendance",
    response_model=BookingResponse,
)
def mark_attendance_endpoint(
    booking_id: UUID,
    payload: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return mark_attendance(
        db=db,
        booking_id=booking_id,
        attendance_status=payload.status,
        user_id=current_user.id,
    )