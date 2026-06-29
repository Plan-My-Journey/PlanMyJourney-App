from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import AuthResponse, LoginRequest, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

_HARDCODED_USER = UserRead(
    id="user-preethi-001",
    name="preethi",
    email="preethikgowda26@gmail.com",
    created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
)
_HARDCODED_EMAIL = "preethikgowda26@gmail.com"
_HARDCODED_PASSWORD = "Preethigowda@26"


def _hardcoded_auth_response() -> AuthResponse:
    token = create_access_token(_HARDCODED_USER.id, {"email": _HARDCODED_USER.email})
    return AuthResponse(access_token=token, user=_HARDCODED_USER)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
    if payload.email == _HARDCODED_EMAIL:
        return _hardcoded_auth_response()

    repository = UserRepository(db)
    if repository.get_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = repository.create(payload.name, payload.email, hash_password(payload.password))
    token = create_access_token(user.id, {"email": user.email})
    return AuthResponse(access_token=token, user=user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
    if payload.email == _HARDCODED_EMAIL and payload.password == _HARDCODED_PASSWORD:
        return _hardcoded_auth_response()

    repository = UserRepository(db)
    user = repository.get_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user.id, {"email": user.email})
    return AuthResponse(access_token=token, user=user)
