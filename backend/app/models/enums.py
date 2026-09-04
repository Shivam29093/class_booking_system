from enum import Enum


class UserRole(str, Enum):

    STAFF = "STAFF"

    INSTRUCTOR = "INSTRUCTOR"


class BookingStatus(str, Enum):

    BOOKED = "BOOKED"

    WAITLISTED = "WAITLISTED"

    CANCELLED = "CANCELLED"

    ATTENDED = "ATTENDED"

    NO_SHOW = "NO_SHOW"


class BookingEventType(str, Enum):

    CREATED = "CREATED"

    CONFIRMED = "CONFIRMED"

    WAITLISTED = "WAITLISTED"

    CANCELLED = "CANCELLED"

    PROMOTED = "PROMOTED"

    ATTENDANCE_MARKED = "ATTENDANCE_MARKED"