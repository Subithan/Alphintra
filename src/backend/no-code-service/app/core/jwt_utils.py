"""JWT utility functions for local token parsing and user extraction."""

import base64
import json
import logging
from typing import Any, Dict, Optional

import jwt
from jwt import PyJWTError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token locally without verification for user extraction.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload as dictionary, or None if decoding fails
    """
    try:
        # Decode without verification to extract payload
        # This is safe since we're only extracting user info, not trusting the token
        # The actual validation still happens via auth service
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except PyJWTError as e:
        logger.warning(f"Failed to decode JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error decoding JWT token: {e}")
        return None


def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from JWT token.

    Args:
        token: JWT token string

    Returns:
        User ID as string, or None if extraction fails
    """
    payload = decode_jwt_token(token)
    if not payload:
        return None

    # Try different common user ID fields
    user_id_fields = ['sub', 'user_id', 'userId', 'id']

    for field in user_id_fields:
        if field in payload:
            user_id = payload[field]
            if isinstance(user_id, (str, int)):
                return str(user_id)

    logger.warning(f"No user ID found in JWT token payload: {payload.keys()}")
    return None


def extract_user_claims(token: str) -> Dict[str, Any]:
    """
    Extract all user claims from JWT token.

    Args:
        token: JWT token string

    Returns:
        Dictionary containing user claims, empty dict if extraction fails
    """
    payload = decode_jwt_token(token)
    if not payload:
        return {}

    claims = {}

    # Extract standard claims
    if 'sub' in payload:
        claims['user_id'] = str(payload['sub'])
    if 'email' in payload:
        claims['email'] = payload['email']
    if 'name' in payload:
        claims['name'] = payload['name']
    if 'roles' in payload:
        claims['roles'] = payload['roles']
    elif 'role' in payload:
        claims['roles'] = [payload['role']]

    # Extract custom claims
    custom_fields = ['first_name', 'last_name', 'is_verified', 'organization']
    for field in custom_fields:
        if field in payload:
            claims[field] = payload[field]

    return claims


def extract_user_info_from_headers(authorization_header: str) -> Dict[str, Any]:
    """
    Extract user information from Authorization header.

    Args:
        authorization_header: Authorization header value (e.g., "Bearer <token>")

    Returns:
        Dictionary containing user information
    """
    if not authorization_header or not authorization_header.startswith("Bearer "):
        return {}

    token = authorization_header[7:]  # Remove "Bearer " prefix
    return extract_user_claims(token)


def validate_token_structure(token: str) -> bool:
    """
    Basic validation of JWT token structure.

    Args:
        token: JWT token string

    Returns:
        True if token has valid JWT structure, False otherwise
    """
    if not token:
        return False

    # JWT should have 3 parts separated by dots
    parts = token.split('.')
    if len(parts) != 3:
        return False

    try:
        # Try to decode header to verify it's valid base64
        header_data = base64.urlsafe_b64decode(parts[0] + '==')
        header = json.loads(header_data)
        return 'alg' in header and 'typ' in header
    except Exception:
        return False


def get_user_context_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Get complete user context from JWT token.

    Args:
        token: JWT token string

    Returns:
        User context dictionary or None if extraction fails
    """
    if not validate_token_structure(token):
        return None

    user_id = extract_user_id_from_token(token)
    if not user_id:
        return None

    claims = extract_user_claims(token)

    return {
        'user_id': user_id,
        'claims': claims,
        'token_valid': True
    }