from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import PreferenceRead, PreferenceUpdate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserRead)
def get_profile(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.put("/profile", response_model=UserRead)
def update_profile(
    payload: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    repository = UserRepository(db)
    if payload.email and payload.email.lower() != current_user.email:
        existing = repository.get_by_email(payload.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already in use")
    return repository.update_profile(current_user, payload.name, str(payload.email) if payload.email else None)


@router.get("/preferences", response_model=PreferenceRead)
def get_preferences(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    repository = UserRepository(db)
    preferences = repository.get_preferences(current_user.id)
    if preferences is None:
        preferences = repository.upsert_preferences(current_user.id, "balanced", 0, [])
    return preferences


@router.put("/preferences", response_model=PreferenceRead)
def update_preferences(
    payload: PreferenceUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    normalized_interests = sorted({interest.strip().lower() for interest in payload.interests if interest.strip()})
    return UserRepository(db).upsert_preferences(
        current_user.id,
        payload.travel_style,
        payload.preferred_budget,
        normalized_interests,
    )
