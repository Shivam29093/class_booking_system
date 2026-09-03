from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    require_staff,
)
from app.core.database import get_db
from app.models.class_model import ClassModel
from app.models.user import User
from app.schemas.class_schema import (
    ClassCreate,
    ClassResponse,
    ClassUpdate,
)


router = APIRouter(
    prefix="/classes",
    tags=["Classes"],
)


@router.post(
    "",
    response_model=ClassResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class(
    class_data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    new_class = ClassModel(
        title=class_data.title,
        description=class_data.description,
        discipline=class_data.discipline,
        default_duration_minutes=class_data.default_duration_minutes,
        default_capacity=class_data.default_capacity,
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    return new_class


@router.get(
    "",
    response_model=list[ClassResponse],
)
def list_classes(
    include_archived: bool = Query(
        default=False,
        description="Include archived classes",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ClassModel)

    if not include_archived:
        query = query.filter(ClassModel.is_archived.is_(False))

    return query.order_by(ClassModel.title.asc()).all()


@router.get(
    "/{class_id}",
    response_model=ClassResponse,
)
def get_class(
    class_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    class_model = db.get(ClassModel, class_id)

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    return class_model


@router.put(
    "/{class_id}",
    response_model=ClassResponse,
)
def update_class(
    class_id: UUID,
    class_data: ClassUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    class_model = db.get(ClassModel, class_id)

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    update_data = class_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(class_model, field, value)

    db.commit()
    db.refresh(class_model)

    return class_model


@router.post(
    "/{class_id}/archive",
    response_model=ClassResponse,
)
def archive_class(
    class_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    class_model = db.get(ClassModel, class_id)

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    if class_model.is_archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class is already archived",
        )

    class_model.is_archived = True

    db.commit()
    db.refresh(class_model)

    return class_model


@router.post(
    "/{class_id}/restore",
    response_model=ClassResponse,
)
def restore_class(
    class_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    class_model = db.get(ClassModel, class_id)

    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    if not class_model.is_archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class is not archived",
        )

    class_model.is_archived = False

    db.commit()
    db.refresh(class_model)

    return class_model