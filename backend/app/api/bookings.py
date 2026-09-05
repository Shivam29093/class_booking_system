from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    require_instructor_or_staff,
    require_staff,
)
from app.core.database import get_db
from app.models.booking import Booking
from app.models.booking_history import BookingHistory
from app.models.class_model import ClassModel
from app.models.instructor import Instructor
from app.models.member import Member
from app.models.session import ClassSession
from app.models.user import User
from app.models.enums import BookingEventType, BookingStatus, UserRole
from app.schemas.booking import (
    AttendanceUpdate,
    BookingNoteCreate,
    BookingCreate,
    BookingHistoryResponse,
    BookingListResponse,
    BookingResponse,
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
    response_model=BookingListResponse,
)
def list_bookings(
    search: str | None = Query(
        default=None,
        description="Search by member name or email",
    ),
    class_id: UUID | None = Query(default=None),
    session_id: UUID | None = Query(default=None),
    booking_status: BookingStatus | None = Query(
        default=None,
        alias="status",
    ),
    sort_by: Literal["booked_at", "status", "session"] = "booked_at",
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor_or_staff),
):
    query = (
        db.query(Booking)
        .join(ClassSession, Booking.session_id == ClassSession.id)
        .join(Member, Booking.member_id == Member.id)
        .join(ClassModel, ClassSession.class_id == ClassModel.id)
    )

    # Instructors can only see bookings for sessions
    # where they are primary or co-instructors.
    if current_user.role == UserRole.INSTRUCTOR:
        instructor = (
            db.query(Instructor)
            .filter(Instructor.user_id == current_user.id)
            .first()
        )

        if not instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Instructor profile not found",
            )

        query = query.filter(
            or_(
                ClassSession.primary_instructor_id == instructor.id,
                ClassSession.instructors.any(
                    Instructor.id == instructor.id
                ),
            )
        )

    # Search member name/email.
    if search:
        search_term = f"%{search.strip()}%"

        query = query.filter(
            or_(
                Member.name.ilike(search_term),
                Member.email.ilike(search_term),
            )
        )

    # Filter by class.
    if class_id:
        query = query.filter(
            ClassSession.class_id == class_id
        )

    # Filter by session.
    if session_id:
        query = query.filter(
            Booking.session_id == session_id
        )

    # Filter by booking status.
    if booking_status:
        query = query.filter(
            Booking.status == booking_status
        )

    # Total BEFORE pagination.
    total = query.count()

    # Sorting.
    if sort_by == "booked_at":
        sort_column = Booking.booked_at
    elif sort_by == "status":
        sort_column = Booking.status
    else:
        sort_column = (
            ClassSession.session_date,
            ClassSession.start_time,
        )

    if sort_by == "session":
        if sort_order == "asc":
            query = query.order_by(
                ClassSession.session_date.asc(),
                ClassSession.start_time.asc(),
                Booking.id.asc(),
            )
        else:
            query = query.order_by(
                ClassSession.session_date.desc(),
                ClassSession.start_time.desc(),
                Booking.id.desc(),
            )
    else:
        if sort_order == "asc":
            query = query.order_by(sort_column.asc(), Booking.id.asc())
        else:
            query = query.order_by(sort_column.desc(), Booking.id.desc())

    # Pagination.
    offset = (page - 1) * page_size

    items = (
        query
        .offset(offset)
        .limit(page_size)
        .all()
    )

    pages = (total + page_size - 1) // page_size

    return BookingListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
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
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if current_user.role == UserRole.INSTRUCTOR:
        instructor = current_user.instructor
        if not instructor or not (
            booking.session.primary_instructor_id == instructor.id
            or any(item.id == instructor.id for item in booking.session.instructors)
        ):
            raise HTTPException(status_code=403, detail="You are not assigned to this session")
    elif current_user.role != UserRole.STAFF:
        raise HTTPException(status_code=403, detail="Staff or instructor access required")
    return mark_attendance(
        db=db,
        booking_id=booking_id,
        attendance_status=payload.status,
        user_id=current_user.id,
    )


@router.post(
    "/{booking_id}/history/notes",
    response_model=BookingHistoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_booking_note(
    booking_id: UUID,
    payload: BookingNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    history = BookingHistory(
        booking_id=booking.id,
        event_type=BookingEventType.STAFF_NOTE,
        note=payload.note.strip(),
        changed_by_user_id=current_user.id,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history