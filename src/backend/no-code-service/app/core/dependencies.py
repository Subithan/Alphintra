"""Common FastAPI dependencies used across routers."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .db import get_db
from .http import get_http_client
from .jwt_utils import extract_user_id_from_token, extract_user_claims
from .redis import get_redis_client

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def get_settings_dependency() -> Settings:
    """Expose application settings as dependency."""

    return get_settings()


def get_redis_dependency():
    """Expose Redis client (or None) as dependency."""

    return get_redis_client()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Any:
    """Return a default/local user without enforcing authentication.

    All requests are allowed; a test user is created/returned if missing.
    """
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
