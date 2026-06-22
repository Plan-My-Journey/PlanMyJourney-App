from dataclasses import dataclass
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str | None
    roles: list[str]


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid authentication token") from exc
