"""Common FastAPI dependencies used across routers."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .config import Settings, get_settings
from .db import get_db
from .http import get_http_client
from .jwt_utils import extract_user_id_from_token, extract_user_claims
from .redis import get_redis_client

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


@dataclass
class TokenUser:
    """Lightweight user representation derived from JWT claims."""

    id: int
    email: Optional[str] = None
    claims: Optional[dict] = None


def get_settings_dependency() -> Settings:
    """Expose application settings as dependency."""

    return get_settings()


def get_redis_dependency():
    """Expose Redis client (or None) as dependency."""

    return get_redis_client()


def _ensure_dev_user(db: Session) -> Any:
    """Create or return the development user for local testing."""

    from models import User  # Lazy import to avoid circular dependency

    test_email = "dev@alphintra.com"
    user = db.query(User).filter(User.email == test_email).first()
    if not user:
        user = User(
            email=test_email,
            password_hash="dev_hash",
            first_name="Development",
            last_name="User",
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> Any:
    """Resolve the caller from the Authorization header.

    When ``DEV_MODE`` is enabled we fall back to a local development user for
    backwards compatibility. Otherwise the request must present a valid token
    for a user that exists in the database.
    """

    from models import User  # Lazy import to avoid circular dependency

    def _unauthorized(detail: str = "Invalid authentication credentials") -> HTTPException:
        return HTTPException(status_code=401, detail=detail)

    if not credentials or not credentials.credentials:
        if settings.dev_mode:
            logger.debug("No credentials supplied; falling back to dev user")
            return _ensure_dev_user(db)
        raise _unauthorized()

    token = credentials.credentials
    try:
        user_id = extract_user_id_from_token(token)
        claims = extract_user_claims(token) or {}
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error decoding authentication token")
        if settings.dev_mode:
            return _ensure_dev_user(db)
        raise _unauthorized()

    if not user_id and not claims:
        if settings.dev_mode:
            logger.warning("Token missing user identifiers; using dev user in DEV_MODE")
            return _ensure_dev_user(db)
        raise _unauthorized()

    user: Optional[User] = None

    if user_id:
        if user_id.isdigit():
            user = db.query(User).filter(User.id == int(user_id)).first()
        else:
            try:
                uuid_value = uuid.UUID(user_id)
            except ValueError:
                uuid_value = None
            if uuid_value:
                user = db.query(User).filter(User.uuid == uuid_value).first()

    if not user and claims:
        email = claims.get("email")
        if email:
            user = db.query(User).filter(User.email == email).first()

    if user:
        return user

    if user_id and user_id.isdigit():
        logger.info("Creating placeholder user for token subject %s", user_id)
        email = (claims or {}).get("email") or f"user-{user_id}@token.local"
        try:
            placeholder_user = User(
                id=int(user_id),
                email=email,
                password_hash="token_user_placeholder",
                first_name=(claims or {}).get("given_name") or (claims or {}).get("first_name"),
                last_name=(claims or {}).get("family_name") or (claims or {}).get("last_name"),
                is_verified=True,
            )
            db.add(placeholder_user)
            db.commit()
            db.refresh(placeholder_user)
            return placeholder_user
        except IntegrityError:
            logger.warning(
                "Placeholder user creation raced with existing record for id %s; refetching",
                user_id,
            )
            db.rollback()
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                return user
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Failed to create placeholder user for token subject %s", user_id)
            db.rollback()
        # Fall back to lightweight token user representation
        return TokenUser(id=int(user_id), email=email, claims=claims)

    if settings.dev_mode:
        logger.warning("Token resolved no user; returning dev user in DEV_MODE")
        return _ensure_dev_user(db)

    raise _unauthorized()


def get_user_context(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Return permissive user context even without credentials."""
    user_id = None
    claims = {}
    token = None
    if credentials and credentials.credentials:
        try:
            token = credentials.credentials
            # Best-effort extraction; ignore failures
            user_id = extract_user_id_from_token(token)
            claims = extract_user_claims(token) or {}
        except Exception:
            user_id = None
            claims = {}
    return {'user_id': user_id, 'claims': claims, 'token': token}
