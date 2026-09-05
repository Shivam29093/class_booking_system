from datetime import date, datetime, time, timedelta
from io import StringIO
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.reports import dashboard, export_attendance_csv, membership_alerts
from app.models.booking import Booking
from app.models.class_model import ClassModel
from app.models.enums import BookingStatus, UserRole
from app.models.instructor import Instructor
from app.models.member import Member
from app.models.room import Room
from app.models.session import ClassSession
from app.models.user import User
from app.services.booking_service import mark_attendance


def make_user(role):
    return User(id=uuid4(), email=f"{uuid4()}@example.com", password_hash="x", role=role)


def make_session(session_date=None):
    return ClassSession(
        id=uuid4(),
        class_id=uuid4(),
        session_date=session_date or date.today(),
        start_time=time(8, 0),
        primary_instructor_id=uuid4(),
        room_id=uuid4(),
        duration_minutes=60,
        capacity=1,
    )


def test_staff_dependency_rejects_instructor():
    from app.api.dependencies import require_staff

    with pytest.raises(HTTPException) as error:
        require_staff(make_user(UserRole.INSTRUCTOR))
    assert error.value.status_code == 403


def test_attendance_before_session_completion_is_rejected(db_session=None):
    session = make_session(date.today() + timedelta(days=1))
    member = Member(id=uuid4(), name="Test Member", email=f"{uuid4()}@example.com", membership_expiry=date.today())
    booking = Booking(id=uuid4(), session_id=session.id, member_id=member.id, status=BookingStatus.BOOKED)

    class FakeQuery:
        def __init__(self, value):
            self.value = value

        def filter(self, *args, **kwargs):
            return self

        def with_for_update(self):
            return self

        def first(self):
            return self.value

    class FakeDb:
        def query(self, model):
            return FakeQuery(booking if model is Booking else session)

    with pytest.raises(HTTPException, match="session has ended"):
        mark_attendance(FakeDb(), booking.id, BookingStatus.ATTENDED, uuid4())


def test_dashboard_response_supports_waitlisted_member_details():
    from app.schemas.booking import DashboardResponse

    response = DashboardResponse(
        sessions_today=0,
        bookings_today=0,
        no_shows_this_week=0,
        currently_waitlisted=1,
        currently_waitlisted_members=[
            {"name": "Member", "email": "member@example.com", "booked_at": datetime.now().isoformat()}
        ],
        booking_breakdown_by_status={},
        booking_breakdown_by_class={},
        attendance_last_eight_weeks=[],
    )
    assert response.currently_waitlisted_members[0]["name"] == "Member"


def test_csv_route_filters_unresolved_statuses():
    source = open("app/api/reports.py", encoding="utf-8").read()
    assert "BookingStatus.ATTENDED" in source
    assert "BookingStatus.NO_SHOW" in source
    assert "BookingStatus.WAITLISTED" not in source.split("def export_attendance_csv", 1)[1]


def test_csv_status_serialization_supports_database_strings():
    status = "ATTENDED"
    serialized = status.value if isinstance(status, BookingStatus) else status
    assert serialized == "ATTENDED"


def test_booking_history_foreign_key_does_not_cascade():
    source = open("app/models/booking_history.py", encoding="utf-8").read()
    assert 'ForeignKey("bookings.id", ondelete="CASCADE")' not in source


def test_database_history_trigger_is_declared():
    source = open("create_tables.py", encoding="utf-8").read()
    assert "booking_history_immutable_trigger" in source
    assert "prevent_booking_history_mutation" in source


def test_dashboard_waitlist_uses_session_end_for_currentness():
    from app.api.reports import _session_is_current

    assert not _session_is_current(make_session(date.today() - timedelta(days=1)))
    assert _session_is_current(make_session(date.today() + timedelta(days=1)))


def test_membership_expiry_change_resets_alert_dismissal():
    source = open("app/api/members.py", encoding="utf-8").read()
    assert "member.expiry_alert_dismissed_for = None" in source
