"""
GraphQL Gateway Security Middleware
Implements JWT authentication, user context, and authorization for GraphQL operations
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import logging
import os
import json
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import strawberry
from strawberry.types import Info

logger = logging.getLogger(__name__)

# Security configuration
INTERNAL_SERVICE_TOKEN = os.getenv('INTERNAL_SERVICE_TOKEN', 'alphintra-internal-token-2024')
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service.alphintra.svc.cluster.local:8080")
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# HTTP client for auth service communication
auth_client = httpx.AsyncClient(timeout=10.0)

class UserContext:
    """User context for authenticated requests"""
    
    def __init__(self, user_id: str, username: str, email: str, roles: list, permissions: list):
        self.id = user_id
        self.username = username
        self.email = email
        self.roles = roles
        self.permissions = permissions
        self.is_admin = 'ADMIN' in roles
        self.is_trader = 'TRADER' in roles
        self.is_viewer = 'VIEWER' in roles

    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions

    def can_access_user_data(self, target_user_id: str) -> bool:
        """Check if user can access data for target user"""
        return self.id == target_user_id or self.is_admin

class GraphQLSecurityMiddleware:
    """
    Middleware to enforce security for GraphQL Gateway
    """
    
    def __init__(self, app, strict_mode: bool = True):
        self.app = app
        self.strict_mode = strict_mode
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        request = Request(scope, receive)
        
        # Skip security for health checks and documentation
        if request.url.path in ['/health', '/status', '/docs', '/openapi.json', '/metrics']:
            await self.app(scope, receive, send)
            return
        
        # Validate gateway routing
        if not self._validate_gateway_request(request):
            logger.warning(f"Unauthorized direct access attempt to {request.url.path} from {request.client.host}")
            response = JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Direct access not allowed",
                    "message": "GraphQL requests must go through the API Gateway",
                    "status": 403
                }
            )
            await response(scope, receive, send)
            return
        
        # For GraphQL endpoints, validate JWT token
        if request.url.path.startswith('/graphql'):
            try:
                user_context = await self._validate_jwt_token(request)
                # Add user context to request state
                request.state.user = user_context
                logger.info(f"Authenticated GraphQL request from user {user_context.id}")
            except HTTPException as e:
                response = JSONResponse(
                    status_code=e.status_code,
                    content={"error": e.detail, "status": e.status_code}
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)

    # In the _validate_gateway_request method around line 85
    def _validate_gateway_request(self, request: Request) -> bool:
        """Validate that request came through the API Gateway"""
        gateway_routed = request.headers.get('x-gateway-routed')
        internal_token = request.headers.get('x-internal-service-token')
        
        # Check gateway routing header
        if gateway_routed == 'true':
            return True
        
        # Check internal service token
        if internal_token == INTERNAL_SERVICE_TOKEN:
            return True
        
        # Allow in development mode WITHOUT authentication
        if ENVIRONMENT == 'development':
            logger.warning("Direct access allowed in development mode")
            return True
        
        return False

    async def _validate_jwt_token(self, request: Request) -> UserContext:
        """Validate JWT token and extract user context"""
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token"
            )
        
        if not auth_header.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token format"
            )
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            # Validate token with auth service
            response = await auth_client.post(
                f"{AUTH_SERVICE_URL}/api/auth/validate",
                json={"token": token},
                headers={
                    "x-gateway-routed": "true",
                    "x-internal-service-token": INTERNAL_SERVICE_TOKEN
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            
            user_data = response.json()
            return UserContext(
                user_id=str(user_data['user_id']),
                username=user_data['username'],
                email=user_data['email'],
                roles=user_data.get('roles', []),
                permissions=user_data.get('permissions', [])
            )
            
        except httpx.TimeoutException:
            logger.error("Auth service timeout during token validation")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )

def get_current_user(info: Info) -> UserContext:
    """Get current user context from GraphQL Info"""
    if not hasattr(info.context['request'], 'state') or not hasattr(info.context['request'].state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return info.context['request'].state.user

def require_role(required_role: str):
    """Decorator to require specific role for GraphQL operations"""
    def decorator(resolver_func):
        async def wrapper(*args, **kwargs):
            info = None
            # Find Info object in args
            for arg in args:
                if isinstance(arg, Info):
                    info = arg
                    break
            
            if not info:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing GraphQL context"
                )
            
            user = get_current_user(info)
            if not user.has_role(required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: requires {required_role} role"
                )
            
            return await resolver_func(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(required_permission: str):
    """Decorator to require specific permission for GraphQL operations"""
    def decorator(resolver_func):
        async def wrapper(*args, **kwargs):
            info = None
            # Find Info object in args
            for arg in args:
                if isinstance(arg, Info):
                    info = arg
                    break
            
            if not info:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing GraphQL context"
                )
            
            user = get_current_user(info)
            if not user.has_permission(required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: requires {required_permission} permission"
                )
            
            return await resolver_func(*args, **kwargs)
        return wrapper
    return decorator

def require_user_access(user_id_field: str = 'user_id'):
    """Decorator to ensure user can only access their own data"""
    def decorator(resolver_func):
        async def wrapper(*args, **kwargs):
            info = None
            # Find Info object in args
            for arg in args:
                if isinstance(arg, Info):
                    info = arg
                    break
            
            if not info:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing GraphQL context"
                )
            
            user = get_current_user(info)
            
            # Get target user ID from arguments
            target_user_id = kwargs.get(user_id_field)
            if target_user_id and not user.can_access_user_data(str(target_user_id)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: cannot access other user's data"
                )
            
            return await resolver_func(*args, **kwargs)
        return wrapper
    return decorator

def add_security_headers(response):
    """Add security headers to responses"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Service-Response"] = "alphintra-graphql-gateway"
    response.headers["X-Response-Source"] = "graphql-gateway"
    return response

def init_graphql_security(app):
    """Initialize security middleware for GraphQL Gateway"""
    
    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        return add_security_headers(response)
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = datetime.utcnow()
        
        # Log request
        logger.info(f"GraphQL Gateway request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # Log response
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"GraphQL Gateway response: {response.status_code} ({duration:.3f}s)")
        
        return response
    
    logger.info("GraphQL Gateway security initialized")

# GraphQL context provider
async def get_context(request: Request) -> Dict[str, Any]:
    """Provide context for GraphQL resolvers"""
    return {
        "request": request,
        "user": getattr(request.state, 'user', None) if hasattr(request, 'state') else None
    }

# Security configuration for different environments
SECURITY_CONFIG = {
    'development': {
        'strict_gateway_check': False,
        'require_authentication': True,
        'log_level': 'DEBUG'
    },
    'staging': {
        'strict_gateway_check': True,
        'require_authentication': True,
        'log_level': 'INFO'
    },
    'production': {
        'strict_gateway_check': True,
        'require_authentication': True,
        'log_level': 'WARNING'
    }
}

def get_security_config():
    """Get security configuration based on environment"""
    env = os.getenv('ENVIRONMENT', 'development')
    return SECURITY_CONFIG.get(env, SECURITY_CONFIG['development'])