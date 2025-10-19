import os
from typing import Optional
import jwt
from fastapi import Header, HTTPException


JWT_ALG = os.getenv("JWT_ALGORITHM", "HS256")
JWT_SECRET = os.getenv("JWT_SECRET", "")
ALLOW_UNVERIFIED_JWT = os.getenv("ALLOW_UNVERIFIED_JWT", "true").lower() == "true"


def _extract_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def decode_jwt(token: str) -> dict:
    if JWT_SECRET:
        try:
            return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG], options={"verify_aud": False})
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    else:
        if not ALLOW_UNVERIFIED_JWT:
            raise HTTPException(status_code=401, detail="JWT verification not configured")
        try:
            return jwt.decode(token, options={"verify_signature": False, "verify_aud": False})
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user_id(Authorization: Optional[str] = Header(default=None)) -> Optional[str]:
    token = _extract_token(Authorization)
    if not token:
        return None
    claims = decode_jwt(token)
    user_id = claims.get("sub") or claims.get("user_id") or claims.get("uid")
    return user_id
