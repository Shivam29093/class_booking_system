from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_staff
from app.core.database import get_db
from app.core.security import hash_password
from app.models.instructor import Instructor
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.instructor import (
    InstructorCreate,
    InstructorResponse,
    InstructorUpdate,
)

router = APIRouter(
    prefix="/instructors",
    tags=["Instructors"],
)


@router.post(
    "",
    response_model=InstructorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_instructor(
    data: InstructorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.INSTRUCTOR,
    )

    db.add(user)
    db.flush()

    instructor = Instructor(
        user_id=user.id,
        name=data.name,
    )

    db.add(instructor)

    try:
        db.commit()
        db.refresh(instructor)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create instructor",
        )

    return instructor


@router.get(
    "",
    response_model=list[InstructorResponse],
)
def list_instructors(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    instructors = (
        db.query(Instructor)
        .join(User, Instructor.user_id == User.id)
        .order_by(Instructor.name)
        .all()
    )

    return instructors


@router.get(
    "/{instructor_id}",
    response_model=InstructorResponse,
)
def get_instructor(
    instructor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    instructor = (
        db.query(Instructor)
        .filter(Instructor.id == instructor_id)
        .first()
    )

    if not instructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found",
        )

    return instructor


@router.put(
    "/{instructor_id}",
    response_model=InstructorResponse,
)
def update_instructor(
    instructor_id: UUID,
    data: InstructorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    instructor = (
        db.query(Instructor)
        .filter(Instructor.id == instructor_id)
        .first()
    )

    if not instructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found",
        )

    if data.name is not None:
        instructor.name = data.name

    if data.email is not None:
        existing_user = (
            db.query(User)
            .filter(
                User.email == data.email,
                User.id != instructor.user_id,
            )
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        instructor.user.email = data.email

    db.commit()
    db.refresh(instructor)

    return instructor