"""
Authentication and authorization utilities.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer()

# Algorithm for JWT encoding/decoding
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time (default: from settings)
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    logger.info("Access token created", user_id=data.get("sub"), expires_at=expire.isoformat())
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Data to encode in the token
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    logger.info("Refresh token created", user_id=data.get("sub"), expires_at=expire.isoformat())
    
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning("Token verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
    """
    Extract user ID from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User ID from token
        
    Raises:
        HTTPException: If token is invalid or missing user ID
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        logger.warning("Token missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = UUID(user_id_str)
        return user_id
    except ValueError:
        logger.warning("Invalid user ID format in token", user_id=user_id_str)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier format",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_with_permissions(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Extract user information and permissions from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User information including permissions
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": UUID(user_id_str),
        "email": payload.get("email"),
        "role": payload.get("role", "user"),
        "permissions": payload.get("permissions", []),
        "is_verified": payload.get("is_verified", False),
        "is_active": payload.get("is_active", True),
    }


def require_permission(permission: str):
    """
    Decorator factory for requiring specific permissions.
    
    Args:
        permission: Required permission string
        
    Returns:
        Dependency function that checks for the permission
    """
    async def permission_checker(
        user_info: Dict[str, Any] = Depends(get_current_user_with_permissions)
    ) -> Dict[str, Any]:
        user_permissions = user_info.get("permissions", [])
        user_role = user_info.get("role", "user")
        
        # Admin role has all permissions
        if user_role == "admin":
            return user_info
        
        if permission not in user_permissions:
            logger.warning(
                "Permission denied",
                user_id=str(user_info["user_id"]),
                required_permission=permission,
                user_permissions=user_permissions
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        
        return user_info
    
    return permission_checker


def require_role(role: str):
    """
    Decorator factory for requiring specific roles.
    
    Args:
        role: Required role string
        
    Returns:
        Dependency function that checks for the role
    """
    async def role_checker(
        user_info: Dict[str, Any] = Depends(get_current_user_with_permissions)
    ) -> Dict[str, Any]:
        user_role = user_info.get("role", "user")
        
        if user_role != role and user_role != "admin":
            logger.warning(
                "Role access denied",
                user_id=str(user_info["user_id"]),
                required_role=role,
                user_role=user_role
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role}"
            )
        
        return user_info
    
    return role_checker


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[UUID]:
    """
    Extract user ID from JWT token if present, but don't require authentication.
    
    Args:
        credentials: Optional HTTP authorization credentials
        
    Returns:
        User ID if token is valid, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id_str = payload.get("sub")
        
        if user_id_str:
            return UUID(user_id_str)
    except (HTTPException, ValueError):
        # Token is invalid, but we don't require auth
        pass
    
    return None


class RateLimiter:
    """Simple in-memory rate limiter for API endpoints."""
    
    def __init__(self):
        self._requests = {}
    
    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Unique identifier for rate limiting (e.g., user_id, IP)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        if key not in self._requests:
            self._requests[key] = []
        
        # Remove old requests outside the window
        self._requests[key] = [
            req_time for req_time in self._requests[key]
            if req_time > window_start
        ]
        
        # Check if limit is exceeded
        if len(self._requests[key]) >= limit:
            return False
        
        # Add current request
        self._requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


def create_rate_limit_dependency(requests_per_minute: int = None):
    """
    Create a rate limiting dependency.
    
    Args:
        requests_per_minute: Override default rate limit
        
    Returns:
        Dependency function for rate limiting
    """
    limit = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
    
    async def rate_limit_check(
        user_id: UUID = Depends(get_current_user_id)
    ):
        key = f"user:{user_id}"
        
        if not rate_limiter.is_allowed(key, limit, 60):
            logger.warning("Rate limit exceeded", user_id=str(user_id), limit=limit)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        return user_id
    
    return rate_limit_check