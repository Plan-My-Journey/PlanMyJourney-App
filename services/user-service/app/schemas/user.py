from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None


class PreferenceRead(BaseModel):
    id: str
    user_id: str
    travel_style: str
    preferred_budget: Decimal
    interests: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreferenceUpdate(BaseModel):
    travel_style: str = Field(default="balanced", min_length=2, max_length=80)
    preferred_budget: Decimal = Field(default=Decimal("0"), ge=0)
    interests: list[str] = Field(default_factory=list)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
