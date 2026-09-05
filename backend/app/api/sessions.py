from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user, require_staff
from app.models import (
    Booking,
    ClassModel,
    ClassSession,
    Instructor,
    Room,
    User,
)
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionUpdate,
)

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"],
)


def get_session_end_time(start_time, duration_minutes):
    start_datetime = datetime.combine(
        datetime.today().date(),
        start_time,
    )

    end_datetime = start_datetime + timedelta(
        minutes=duration_minutes
    )

    return end_datetime.time()


def validate_session_conflict(
    db: Session,
    session_date,
    start_time,
    duration_minutes,
    room_id,
    primary_instructor_id,
    exclude_session_id: UUID | None = None,
):
    end_time = get_session_end_time(
        start_time,
        duration_minutes,
    )

    query = db.query(ClassSession).filter(
        ClassSession.session_date == session_date
    )

    if exclude_session_id:
        query = query.filter(
            ClassSession.id != exclude_session_id
        )

    existing_sessions = query.all()

    for existing in existing_sessions:
        existing_end = get_session_end_time(
            existing.start_time,
            existing.duration_minutes,
        )

        # Time overlap:
        # new_start < existing_end AND
        # new_end > existing_start
        time_overlap = (
            start_time < existing_end
            and end_time > existing.start_time
        )

        if not time_overlap:
            continue

        if existing.room_id == room_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Room is already booked during this time",
            )

        if (
            existing.primary_instructor_id
            == primary_instructor_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Instructor is already scheduled during this time",
            )

        # Check co-instructors as well.
        if any(
            instructor.id == primary_instructor_id
            for instructor in existing.instructors
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Instructor is already scheduled during this time",
            )


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    class_obj = (
        db.query(ClassModel)
        .filter(ClassModel.id == data.class_id)
        .first()
    )

    if not class_obj:
        raise HTTPException(
            status_code=404,
            detail="Class not found",
        )

    if class_obj.is_archived:
        raise HTTPException(
            status_code=400,
            detail="Cannot schedule a session for an archived class",
        )

    instructor = (
        db.query(Instructor)
        .filter(Instructor.id == data.primary_instructor_id)
        .first()
    )

    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found",
        )

    room = (
        db.query(Room)
        .filter(Room.id == data.room_id)
        .first()
    )

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    duration = (
        data.duration_minutes
        if data.duration_minutes is not None
        else class_obj.default_duration_minutes
    )

    capacity = (
        data.capacity
        if data.capacity is not None
        else class_obj.default_capacity
    )

    validate_session_conflict(
        db=db,
        session_date=data.session_date,
        start_time=data.start_time,
        duration_minutes=duration,
        room_id=data.room_id,
        primary_instructor_id=data.primary_instructor_id,
    )

    session = ClassSession(
        class_id=data.class_id,
        session_date=data.session_date,
        start_time=data.start_time,
        primary_instructor_id=data.primary_instructor_id,
        room_id=data.room_id,
        duration_minutes=duration,
        capacity=capacity,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.get(
    "",
    response_model=list[SessionResponse],
)
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Staff can see every session.
    if current_user.role == "STAFF":
        return (
            db.query(ClassSession)
            .order_by(
                ClassSession.session_date,
                ClassSession.start_time,
            )
            .all()
        )

    # Instructor can only see sessions where they are
    # primary or co-instructor.
    if current_user.instructor:
        instructor_id = current_user.instructor.id

        return (
            db.query(ClassSession)
            .filter(
                or_(
                    ClassSession.primary_instructor_id
                    == instructor_id,
                    ClassSession.instructors.any(
                        Instructor.id == instructor_id
                    ),
                )
            )
            .order_by(
                ClassSession.session_date,
                ClassSession.start_time,
            )
            .all()
        )

    return []


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(ClassSession)
        .filter(ClassSession.id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    if current_user.role == "STAFF":
        return session

    if not current_user.instructor:
        raise HTTPException(
            status_code=403,
            detail="Instructor access required",
        )

    instructor_id = current_user.instructor.id

    if (
        session.primary_instructor_id != instructor_id
        and not any(
            instructor.id == instructor_id
            for instructor in session.instructors
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this session",
        )

    return session


@router.put(
    "/{session_id}",
    response_model=SessionResponse,
)
def update_session(
    session_id: UUID,
    data: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    session = (
        db.query(ClassSession)
        .filter(ClassSession.id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    new_date = (
        data.session_date
        if data.session_date is not None
        else session.session_date
    )

    new_start = (
        data.start_time
        if data.start_time is not None
        else session.start_time
    )

    new_duration = (
        data.duration_minutes
        if data.duration_minutes is not None
        else session.duration_minutes
    )

    new_room = (
        data.room_id
        if data.room_id is not None
        else session.room_id
    )

    new_instructor = (
        data.primary_instructor_id
        if data.primary_instructor_id is not None
        else session.primary_instructor_id
    )

    if data.primary_instructor_id is not None:
        instructor = (
            db.query(Instructor)
            .filter(
                Instructor.id
                == data.primary_instructor_id
            )
            .first()
        )

        if not instructor:
            raise HTTPException(
                status_code=404,
                detail="Instructor not found",
            )

    if data.room_id is not None:
        room = (
            db.query(Room)
            .filter(Room.id == data.room_id)
            .first()
        )

        if not room:
            raise HTTPException(
                status_code=404,
                detail="Room not found",
            )

    validate_session_conflict(
        db=db,
        session_date=new_date,
        start_time=new_start,
        duration_minutes=new_duration,
        room_id=new_room,
        primary_instructor_id=new_instructor,
        exclude_session_id=session.id,
    )

    if data.session_date is not None:
        session.session_date = data.session_date

    if data.start_time is not None:
        session.start_time = data.start_time

    if data.primary_instructor_id is not None:
        session.primary_instructor_id = (
            data.primary_instructor_id
        )

    if data.room_id is not None:
        session.room_id = data.room_id

    if data.duration_minutes is not None:
        session.duration_minutes = (
            data.duration_minutes
        )

    if data.capacity is not None:
        session.capacity = data.capacity

    db.commit()
    db.refresh(session)

    return session


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    session = (
        db.query(ClassSession)
        .filter(ClassSession.id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    if db.query(Booking).filter(Booking.session_id == session.id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session cannot be deleted because it has booking history",
        )

    db.delete(session)
    db.commit()

    return None
@router.post(
    "/{session_id}/co-instructors/{instructor_id}",
    response_model=SessionResponse,
)
def add_co_instructor(
    session_id: UUID,
    instructor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    session = (
        db.query(ClassSession)
        .filter(ClassSession.id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    instructor = (
        db.query(Instructor)
        .filter(Instructor.id == instructor_id)
        .first()
    )

    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found",
        )

    if session.primary_instructor_id == instructor_id:
        raise HTTPException(
            status_code=400,
            detail="Primary instructor cannot also be a co-instructor",
        )

    if instructor in session.instructors:
        raise HTTPException(
            status_code=409,
            detail="Instructor is already a co-instructor",
        )

    validate_session_conflict(
        db=db,
        session_date=session.session_date,
        start_time=session.start_time,
        duration_minutes=session.duration_minutes,
        room_id=session.room_id,
        primary_instructor_id=instructor_id,
        exclude_session_id=session.id,
    )

    session.instructors.append(instructor)

    db.commit()
    db.refresh(session)

    return session


@router.delete(
    "/{session_id}/co-instructors/{instructor_id}",
    response_model=SessionResponse,
)
def remove_co_instructor(
    session_id: UUID,
    instructor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    session = (
        db.query(ClassSession)
        .filter(ClassSession.id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    instructor = (
        db.query(Instructor)
        .filter(Instructor.id == instructor_id)
        .first()
    )

    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found",
        )

    if instructor not in session.instructors:
        raise HTTPException(
            status_code=404,
            detail="Instructor is not a co-instructor for this session",
        )

    session.instructors.remove(instructor)

    db.commit()
    db.refresh(session)

    return session