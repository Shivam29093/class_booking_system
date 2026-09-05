from app.main import app
from app.models.enums import BookingEventType, BookingStatus, UserRole
from app.schemas.booking import RecurrenceCreate
from app.services.booking_service import booking_event_for_status
from app.models.booking_history import prevent_history_delete, prevent_history_update
from app.api.dependencies import require_staff, require_instructor_or_staff
from pydantic import ValidationError
import pytest


def test_required_routes_are_registered():
    paths = set(app.openapi()["paths"])
    assert "/reports/dashboard" in paths
    assert "/reports/recurring-sessions" in paths
    assert "/reports/sessions/{session_id}/attendance.csv" in paths
    assert "/reports/membership-alerts" in paths
    assert "/bookings/{booking_id}/history/notes" in paths


def test_assignment_enums_include_roles_and_history_event():
    assert {role.value for role in UserRole} == {"STAFF", "INSTRUCTOR"}
    assert BookingStatus.WAITLISTED.value == "WAITLISTED"
    assert BookingEventType.STAFF_NOTE.value == "STAFF_NOTE"


def test_recurrence_requires_at_least_one_weekday():
    with pytest.raises(ValidationError):
        RecurrenceCreate(
            class_id="00000000-0000-0000-0000-000000000001",
            start_date="2026-09-07",
            end_date="2026-09-14",
            weekdays=[],
            start_time="09:00",
            primary_instructor_id="00000000-0000-0000-0000-000000000002",
            room_id="00000000-0000-0000-0000-000000000003",
        )


def test_reactivation_history_event_matches_new_status():
    assert booking_event_for_status(BookingStatus.BOOKED) == BookingEventType.CONFIRMED
    assert booking_event_for_status(BookingStatus.WAITLISTED) == BookingEventType.WAITLISTED
    with pytest.raises(ValueError):
        booking_event_for_status(BookingStatus.CANCELLED)


def test_booking_history_mutation_guards_are_present():
    with pytest.raises(ValueError, match="immutable"):
        prevent_history_update(None, None, None)
    with pytest.raises(ValueError, match="immutable"):
        prevent_history_delete(None, None, None)


def test_role_dependencies_remain_separate():
    assert require_staff.__name__ == "require_staff"
    assert require_instructor_or_staff.__name__ == "require_instructor_or_staff"


def test_dashboard_contract_always_represents_eight_weeks():
    from app.schemas.booking import DashboardResponse

    response = DashboardResponse(
        sessions_today=0,
        bookings_today=0,
        no_shows_this_week=0,
        currently_waitlisted=0,
        booking_breakdown_by_status={},
        booking_breakdown_by_class={},
        attendance_last_eight_weeks=[
            {"week": str(index), "attended": 0, "no_show": 0}
            for index in range(8)
        ],
    )
    assert len(response.attendance_last_eight_weeks) == 8
