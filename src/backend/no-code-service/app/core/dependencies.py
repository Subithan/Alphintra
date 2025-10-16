"""Common FastAPI dependencies used across routers."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .db import get_db
from .http import get_http_client
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
    """Validate JWT token with Auth Service or return mock user in dev mode."""

    settings = get_settings()
    from models import User  # Lazy import to avoid circular dependency

    if settings.dev_mode:
        logger.info("Development mode: using test user")
        test_user = db.query(User).filter(User.email == "dev@alphintra.com").first()
        if not test_user:
            test_user = User(
                email="dev@alphintra.com",
                password_hash="dev_hash",
                first_name="Development",
                last_name="User",
                is_verified=True,
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        return test_user

    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        client = await get_http_client()
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = await client.get(f"{settings.auth_service_url}/api/v1/auth/validate", headers=headers)

        if response.status_code == 200:
            return response.json()

        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error validating token: %s", exc)
        raise HTTPException(status_code=401, detail="Authentication service unavailable") from exc
