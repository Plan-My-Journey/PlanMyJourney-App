from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.request import urlopen
import json

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_jwks_cache: dict[str, Any] | None = None


def _get_cognito_jwks() -> dict[str, Any]:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    if not settings.cognito_issuer_url:
        raise ValueError("Cognito issuer URL is not configured")
    jwks_url = f"{settings.cognito_issuer_url}/.well-known/jwks.json"
    with urlopen(jwks_url, timeout=5) as response:
        _jwks_cache = json.loads(response.read().decode("utf-8"))
    return _jwks_cache


def decode_cognito_token(token: str) -> dict[str, Any]:
    jwks = _get_cognito_jwks()
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if key is None:
        raise ValueError("Unable to find matching Cognito signing key")
    return jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=settings.cognito_app_client_id or None,
        issuer=settings.cognito_issuer_url,
        options={"verify_aud": bool(settings.cognito_app_client_id)},
    )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expires_at, "roles": ["traveler"]}
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    if settings.use_cognito:
        try:
            return decode_cognito_token(token)
        except Exception as exc:
            raise ValueError("Invalid Cognito token") from exc
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid authentication token") from exc
