from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.dependencies import require_staff
from app.core.database import get_db
from app.models.member import Member
from app.models.user import User
from app.schemas.member import (
    MemberCreate,
    MemberResponse,
    MemberUpdate,
)

router = APIRouter(
    prefix="/members",
    tags=["Members"],
)


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_member(
    data: MemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    member = Member(
        name=data.name,
        email=data.email,
        membership_expiry=data.membership_expiry,
    )

    db.add(member)
    db.commit()
    db.refresh(member)

    return member


@router.get(
    "",
    response_model=list[MemberResponse],
)
def list_members(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    query = db.query(Member)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Member.name.ilike(search_term),
                Member.email.ilike(search_term),
            )
        )

    return query.order_by(Member.name).all()


@router.get(
    "/{member_id}",
    response_model=MemberResponse,
)
def get_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    member = db.query(Member).filter(Member.id == member_id).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    return member


@router.put(
    "/{member_id}",
    response_model=MemberResponse,
)
def update_member(
    member_id: UUID,
    data: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    member = db.query(Member).filter(Member.id == member_id).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    if data.name is not None:
        member.name = data.name

    if data.email is not None:
        member.email = data.email

    if data.membership_expiry is not None:
        member.membership_expiry = data.membership_expiry

    db.commit()
    db.refresh(member)

    return member