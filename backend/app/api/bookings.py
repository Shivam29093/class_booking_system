from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_staff
from app.core.database import get_db
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import (
    cancel_booking,
    create_booking,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_booking_endpoint(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff),
):
    return create_booking(
        db=db,
        session_id=payload.session_id,
        member_id=payload.member_id,
        user_id=current_user.id,
    )


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
)
def cancel_booking_endpoint(
    booking_id,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff),
):
    return cancel_booking(
        db=db,
        booking_id=booking_id,
        user_id=current_user.id,
    )