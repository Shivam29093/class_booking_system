from enum import Enum


class UserRole(str, Enum):
    STAFF = "STAFF"
    INSTRUCTOR = "INSTRUCTOR"


class BookingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    WAITLISTED = "WAITLISTED"
    CANCELLED = "CANCELLED"


class BookingEventType(str, Enum):
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    WAITLISTED = "WAITLISTED"
    CANCELLED = "CANCELLED"
    PROMOTED = "PROMOTED"