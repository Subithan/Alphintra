"""
FastAPI Security Middleware for Microservices
Ensures requests only come through the API Gateway
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging
import os
from typing import Callable

logger = logging.getLogger(__name__)

class GatewaySecurityMiddleware:
    """
    Middleware to ensure requests come through the API Gateway
    """
    
    def __init__(self, app, strict_mode: bool = True):
        self.app = app
        self.strict_mode = strict_mode
        self.internal_token = os.getenv('INTERNAL_SERVICE_TOKEN', 'alphintra-internal-token-2024')
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        request = Request(scope, receive)
        
        # Skip security for health checks and internal status
        if request.url.path in ['/health', '/docs', '/openapi.json']:
            await self.app(scope, receive, send)
            return
        
        # Check gateway routing headers
        gateway_routed = request.headers.get('x-gateway-routed')
        request_source = request.headers.get('x-request-source')
        internal_token = request.headers.get('x-internal-service-token')
        
        # Validate request source
        is_valid = False
        
        # Check if request came through gateway
        if gateway_routed == 'true':
            is_valid = True
            logger.info(f"Gateway-routed request to {request.url.path}")
        
        # Check for internal service token (for service-to-service communication)
        elif internal_token == self.internal_token:
            is_valid = True
            logger.info(f"Internal service request to {request.url.path}")
        
        # In development mode, allow direct access
        elif not self.strict_mode and os.getenv('ENVIRONMENT', 'development') == 'development':
            is_valid = True
            logger.warning(f"Direct access allowed in development mode: {request.url.path}")
        
        if not is_valid:
            logger.warning(f"Unauthorized access attempt to {request.url.path} from {request.client.host}")
            response = JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Direct access not allowed",
                    "message": "All requests must go through the API Gateway",
                    "status": 403
                }
            )
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send)

def validate_gateway_request(request: Request) -> bool:
    """
    Validate that the request came through the gateway
    """
    gateway_routed = request.headers.get('x-gateway-routed')
    internal_token = request.headers.get('x-internal-service-token')
    expected_token = os.getenv('INTERNAL_SERVICE_TOKEN', 'alphintra-internal-token-2024')
    
    # Check gateway routing
    if gateway_routed == 'true':
        return True
    
    # Check internal service token
    if internal_token == expected_token:
        return True
    
    # Allow in development mode
    if os.getenv('ENVIRONMENT', 'development') == 'development':
        return True
    
    return False

async def require_gateway_routing(request: Request):
    """
    Dependency to ensure request came through gateway
    """
    if not validate_gateway_request(request):
        logger.warning(f"Unauthorized access attempt to {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Direct access not allowed",
                "message": "All requests must go through the API Gateway"
            }
        )

def add_security_headers(response):
    """
    Add security headers to responses
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Service-Response"] = "alphintra-microservice"
    response.headers["X-Response-Source"] = os.getenv('SERVICE_NAME', 'trading-service')
    return response

def init_microservice_security(app):
    """
    Initialize security for FastAPI microservice
    """
    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        return add_security_headers(response)
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check(request: Request):
        return {
            "status": "healthy",
            "service": os.getenv('SERVICE_NAME', 'trading-service'),
            "request_id": request.headers.get('x-request-id', 'unknown'),
            "gateway_routed": request.headers.get('x-gateway-routed', 'false')
        }
    
    # Add internal status endpoint
    @app.get("/internal/status")
    async def internal_status(request: Request):
        # Validate internal request
        if not validate_gateway_request(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Internal endpoint access denied"
            )
        
        return {
            "status": "operational",
            "service": os.getenv('SERVICE_NAME', 'trading-service'),
            "gateway_routed": request.headers.get('x-gateway-routed', 'false'),
            "request_id": request.headers.get('x-request-id', 'unknown')
        }
    
    logger.info(f"Microservice security initialized for {os.getenv('SERVICE_NAME', 'trading-service')}")

# Security configuration for different environments
SECURITY_CONFIG = {
    'development': {
        'strict_gateway_check': False,
        'allow_direct_access': True,
        'log_level': 'DEBUG'
    },
    'staging': {
        'strict_gateway_check': True,
        'allow_direct_access': False,
        'log_level': 'INFO'
    },
    'production': {
        'strict_gateway_check': True,
        'allow_direct_access': False,
        'log_level': 'WARNING'
    }
}

def get_security_config():
    """Get security configuration based on environment"""
    env = os.getenv('ENVIRONMENT', 'development')
    return SECURITY_CONFIG.get(env, SECURITY_CONFIG['development'])