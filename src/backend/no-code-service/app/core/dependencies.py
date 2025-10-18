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
        # Extract user info locally from JWT for performance
        user_id = extract_user_id_from_token(credentials.credentials)
        user_claims = extract_user_claims(credentials.credentials)

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user ID found")

        # Try to validate with auth service first (for production)
        try:
            client = await get_http_client()
            headers = {"Authorization": f"Bearer {credentials.credentials}"}
            response = await client.get(f"{settings.auth_service_url}/api/v1/auth/validate", headers=headers)

            if response.status_code == 200:
                auth_user = response.json()
                # Merge local extraction with auth service response
                if 'user_id' not in auth_user:
                    auth_user['user_id'] = user_id
                return auth_user
        except Exception as e:
            logger.warning(f"Auth service validation failed, using local JWT extraction: {e}")

        # Fallback to local JWT extraction if auth service is unavailable
        logger.info("Using local JWT extraction for user validation")

        # Try to find user in local database
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            return {
                'id': user.id,
                'uuid': str(user.uuid),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'user_id': user_id,
                **user_claims
            }

        # If user not found locally, create user info from JWT claims
        return {
            'user_id': user_id,
            'email': user_claims.get('email', f'user_{user_id}@example.com'),
            'first_name': user_claims.get('first_name', 'User'),
            'last_name': user_claims.get('last_name', str(user_id)),
            'is_active': True,
            'is_verified': user_claims.get('is_verified', True),
            'roles': user_claims.get('roles', []),
            **user_claims
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error validating token: %s", exc)
        raise HTTPException(status_code=401, detail="Authentication failed") from exc


def get_user_context(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Extract user context from JWT token without database lookup.

    This is a lightweight alternative to get_current_user for operations
    that only need user identification without full user data.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = extract_user_id_from_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: no user ID found")

    user_claims = extract_user_claims(credentials.credentials)

    return {
        'user_id': user_id,
        'claims': user_claims,
        'token': credentials.credentials
    }
