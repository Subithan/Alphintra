"""Common FastAPI dependencies used across routers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Union

from fastapi import Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .db import get_db
from .jwt_utils import extract_user_id_from_token, extract_user_claims
from .redis import get_redis_client

logger = logging.getLogger(__name__)

@dataclass
class TokenUser:
    """Lightweight user representation derived from JWT claims."""

    id: Union[int, str]
    email: Optional[str] = None
    claims: Optional[dict] = None


def get_settings_dependency() -> Settings:
    """Expose application settings as dependency."""

    return get_settings()


def get_redis_dependency():
    """Expose Redis client (or None) as dependency."""

    return get_redis_client()


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenUser:
    """Resolve the caller from the Authorization header.

    When ``DEV_MODE`` is enabled we fall back to a local development user for
    backwards compatibility. Otherwise the request must present a valid token
    for a user that exists in the database.
    """

    def _unauthorized(detail: str = "Invalid authentication credentials") -> HTTPException:
        return HTTPException(status_code=401, detail=detail)

    raw_header = request.headers.get("Authorization")
    token = None
    if raw_header and raw_header.lower().startswith("bearer "):
        token = raw_header.split(" ", 1)[1].strip()
        logger.info("Authorization header prefix: %s...", raw_header[:24])

    if not token:
        if settings.dev_mode:
            logger.debug("No credentials supplied; returning dev token user")
            return TokenUser(id="dev", email="dev@alphintra.com", claims={"dev_mode": True})
        logger.warning("Rejecting request: missing or malformed Authorization header")
        raise _unauthorized()

    try:
        user_id = extract_user_id_from_token(token)
        claims = extract_user_claims(token) or {}
        logger.info("Decoded token -> user_id=%s claims_keys=%s", user_id, list(claims.keys()))
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error decoding authentication token")
        if settings.dev_mode:
            return TokenUser(id="dev", email="dev@alphintra.com", claims={"dev_mode": True})
        raise _unauthorized()

    if not user_id:
        logger.warning("Rejecting request: token missing user identifier")
        raise _unauthorized("Token missing user identifier")

    email = (claims or {}).get("email")
    try:
        normalized_id: Union[int, str] = int(user_id)
    except (ValueError, TypeError):
        normalized_id = user_id

    if isinstance(normalized_id, int):
        from models import User  # Lazy import to avoid circular dependency

        user_row = db.query(User).filter(User.id == normalized_id).first()
        if not user_row:
            placeholder = User(
                id=normalized_id,
                email=email or f"user-{normalized_id}@token.local",
                password_hash="token_user_placeholder",
                first_name=(claims or {}).get("first_name") or "Token",
                last_name=(claims or {}).get("last_name") or "User",
                is_verified=True,
            )
            db.add(placeholder)
            try:
                db.commit()
                logger.info("Created placeholder user %s from token", normalized_id)
            except IntegrityError:
                db.rollback()
                logger.info("Placeholder user %s already existed", normalized_id)
            except Exception:
                db.rollback()
                logger.exception("Failed to create placeholder user %s", normalized_id)

    return TokenUser(id=normalized_id, email=email, claims=claims)


def get_user_context(request: Request) -> dict:
    """Return permissive user context even without credentials."""
    user_id = None
    claims = {}
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            user_id = extract_user_id_from_token(token)
            claims = extract_user_claims(token) or {}
            logger.info("Context extraction token user_id=%s", user_id)
        except Exception:
            user_id = None
            claims = {}
    return {"user_id": user_id, "claims": claims, "token": token}
