from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_staff
from app.core.database import get_db
from app.models.room import Room
from app.models.user import User
from app.schemas.room import RoomCreate, RoomResponse, RoomUpdate

router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"],
)


@router.post(
    "",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_room(
    data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    room = Room(name=data.name.strip())

    db.add(room)

    try:
        db.commit()
        db.refresh(room)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A room with this name already exists",
        )

    return room


@router.get(
    "",
    response_model=list[RoomResponse],
)
def list_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    return db.query(Room).order_by(Room.name).all()


@router.get(
    "/{room_id}",
    response_model=RoomResponse,
)
def get_room(
    room_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    room = db.query(Room).filter(Room.id == room_id).first()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    return room


@router.put(
    "/{room_id}",
    response_model=RoomResponse,
)
def update_room(
    room_id: UUID,
    data: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    room = db.query(Room).filter(Room.id == room_id).first()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    room.name = data.name.strip()

    try:
        db.commit()
        db.refresh(room)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A room with this name already exists",
        )

    return room


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_room(
    room_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    room = db.query(Room).filter(Room.id == room_id).first()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    db.delete(room)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Room cannot be deleted because it is used by a session",
        )