import csv
from datetime import date, datetime, timedelta
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import require_staff
from app.api.sessions import validate_session_conflict
from app.core.database import get_db
from app.models.booking import Booking
from app.models.class_model import ClassModel
from app.models.enums import BookingStatus
from app.models.instructor import Instructor
from app.models.member import Member
from app.models.room import Room
from app.models.session import ClassSession
from app.models.user import User
from app.schemas.booking import (
    DashboardResponse,
    MembershipAlertResponse,
    RecurrenceCreate,
    RecurrenceResult,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


def _session_end(session: ClassSession) -> datetime:
    return datetime.combine(session.session_date, session.start_time) + timedelta(
        minutes=session.duration_minutes
    )


def _session_is_current(session: ClassSession, now: datetime | None = None) -> bool:
    return _session_end(session) > (now or datetime.now())


@router.post("/recurring-sessions", response_model=RecurrenceResult)
def create_recurring_sessions(
    payload: RecurrenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="End date must be on or after start date")
    if any(day < 0 or day > 6 for day in payload.weekdays):
        raise HTTPException(status_code=422, detail="Weekdays must use values 0 through 6")

    class_obj = db.get(ClassModel, payload.class_id)
    instructor = db.get(Instructor, payload.primary_instructor_id)
    room = db.get(Room, payload.room_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    if class_obj.is_archived:
        raise HTTPException(status_code=400, detail="Cannot schedule an archived class")
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    duration = payload.duration_minutes or class_obj.default_duration_minutes
    capacity = payload.capacity or class_obj.default_capacity
    created_ids: list[UUID] = []
    skipped: list[dict[str, str]] = []
    current_date = payload.start_date

    while current_date <= payload.end_date:
        if current_date.weekday() in payload.weekdays:
            try:
                validate_session_conflict(
                    db=db,
                    session_date=current_date,
                    start_time=payload.start_time,
                    duration_minutes=duration,
                    room_id=payload.room_id,
                    primary_instructor_id=payload.primary_instructor_id,
                )
                session = ClassSession(
                    class_id=payload.class_id,
                    session_date=current_date,
                    start_time=payload.start_time,
                    primary_instructor_id=payload.primary_instructor_id,
                    room_id=payload.room_id,
                    duration_minutes=duration,
                    capacity=capacity,
                )
                db.add(session)
                db.flush()
                created_ids.append(session.id)
            except HTTPException as error:
                skipped.append({"date": current_date.isoformat(), "reason": str(error.detail)})
        current_date += timedelta(days=1)

    db.commit()
    return RecurrenceResult(
        created_session_ids=created_ids,
        created_count=len(created_ids),
        skipped=skipped,
    )


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    eight_weeks_ago = today - timedelta(days=55)

    sessions_today = db.query(ClassSession).filter(ClassSession.session_date == today).count()
    bookings_today = (
        db.query(Booking)
        .join(ClassSession)
        .filter(func.date(Booking.booked_at) == today)
        .count()
    )
    no_shows = (
        db.query(Booking)
        .join(ClassSession)
        .filter(
            Booking.status == BookingStatus.NO_SHOW,
            ClassSession.session_date >= week_start,
            ClassSession.session_date <= today,
        )
        .count()
    )
    waitlisted_members = (
        db.query(Member.name, Member.email, Booking.booked_at, ClassSession)
        .join(Booking, Booking.member_id == Member.id)
        .join(ClassSession, Booking.session_id == ClassSession.id)
        .filter(Booking.status == BookingStatus.WAITLISTED)
        .order_by(Booking.booked_at.asc())
        .all()
    )
    current_waitlisted_members = [
        (name, email, booked_at)
        for name, email, booked_at, session in waitlisted_members
        if _session_is_current(session)
    ]
    waitlisted = len(current_waitlisted_members)

    status_rows = (
        db.query(Booking.status, func.count(Booking.id))
        .group_by(Booking.status)
        .all()
    )
    class_rows = (
        db.query(ClassModel.title, func.count(Booking.id))
        .join(ClassSession, ClassSession.class_id == ClassModel.id)
        .join(Booking, Booking.session_id == ClassSession.id)
        .group_by(ClassModel.title)
        .order_by(ClassModel.title)
        .all()
    )

    attendance = (
        db.query(ClassSession.session_date, Booking.status, func.count(Booking.id))
        .join(Booking, Booking.session_id == ClassSession.id)
        .filter(
            ClassSession.session_date >= eight_weeks_ago,
            Booking.status.in_([BookingStatus.ATTENDED, BookingStatus.NO_SHOW]),
        )
        .group_by(ClassSession.session_date, Booking.status)
        .all()
    )
    weekly: dict[str, dict[str, int]] = {}
    for session_date, booking_status, count in attendance:
        monday = session_date - timedelta(days=session_date.weekday())
        key = monday.isoformat()
        weekly.setdefault(key, {"attended": 0, "no_show": 0})
        if booking_status == BookingStatus.ATTENDED:
            weekly[key]["attended"] += count
        else:
            weekly[key]["no_show"] += count

    current_week = today - timedelta(days=today.weekday())
    attendance_chart = []
    for offset in range(7, -1, -1):
        week = (current_week - timedelta(weeks=offset)).isoformat()
        attendance_chart.append(
            {"week": week, **weekly.get(week, {"attended": 0, "no_show": 0})}
        )
    return DashboardResponse(
        sessions_today=sessions_today,
        bookings_today=bookings_today,
        no_shows_this_week=no_shows,
        currently_waitlisted=waitlisted,
        currently_waitlisted_members=[
            {
                "name": name,
                "email": email,
                "booked_at": booked_at.isoformat(),
            }
            for name, email, booked_at in current_waitlisted_members
        ],
        booking_breakdown_by_status={
            key.value if isinstance(key, BookingStatus) else str(key): value
            for key, value in status_rows
        },
        booking_breakdown_by_class={key: value for key, value in class_rows},
        attendance_last_eight_weeks=attendance_chart,
    )


@router.get("/membership-alerts", response_model=list[MembershipAlertResponse])
def membership_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    today = date.today()
    members = (
        db.query(Member)
        .filter(
            Member.membership_expiry <= today + timedelta(days=7),
            (Member.expiry_alert_dismissed_for.is_(None))
            | (Member.expiry_alert_dismissed_for != Member.membership_expiry),
        )
        .order_by(Member.membership_expiry, Member.name)
        .all()
    )
    return [
        MembershipAlertResponse(
            member_id=member.id,
            member_name=member.name,
            member_email=member.email,
            membership_expiry=member.membership_expiry,
            days_remaining=(member.membership_expiry - today).days,
        )
        for member in members
    ]


@router.post("/membership-alerts/{member_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_membership_alert(
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.expiry_alert_dismissed_for = member.membership_expiry
    db.commit()
    return None


@router.get("/sessions/{session_id}/attendance.csv")
def export_attendance_csv(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    session = db.get(ClassSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["member_name", "member_email", "status", "booked_at"])
    bookings = (
        db.query(Booking)
        .join(Member)
        .filter(
            Booking.session_id == session_id,
            Booking.status.in_([BookingStatus.ATTENDED, BookingStatus.NO_SHOW]),
        )
        .order_by(Member.name)
        .all()
    )
    for booking in bookings:
        writer.writerow([
            booking.member.name,
            booking.member.email,
            booking.status.value if isinstance(booking.status, BookingStatus) else booking.status,
            booking.booked_at.isoformat(),
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="session-{session_id}-attendance.csv"'},
    )
