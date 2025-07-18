"""
Microservice Security Module
Ensures requests only come through the API Gateway
"""

from functools import wraps
from flask import request, jsonify, current_app
import logging
import os

logger = logging.getLogger(__name__)

class GatewaySecurityError(Exception):
    """Raised when a request doesn't come through the gateway"""
    pass

def require_gateway_routing(f):
    """
    Decorator to ensure requests come through the API Gateway
    Checks for gateway-specific headers
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get expected gateway headers
        gateway_routed = request.headers.get('X-Gateway-Routed')
        request_source = request.headers.get('X-Request-Source')
        service_type = request.headers.get('X-Service-Type')
        
        # Check if request came through gateway
        if not gateway_routed or gateway_routed != 'true':
            logger.warning(f"Direct access attempt from {request.remote_addr} to {request.endpoint}")
            return jsonify({
                'error': 'Direct access not allowed',
                'message': 'All requests must go through the API Gateway',
                'status': 403
            }), 403
        
        # Log gateway-routed request
        logger.info(f"Gateway-routed request: {service_type} service from {request.remote_addr}")
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_internal_request():
    """
    Validate that the request is internal (from gateway or another microservice)
    Returns True if valid, False otherwise
    """
    # Check for gateway routing header
    if request.headers.get('X-Gateway-Routed') == 'true':
        return True
    
    # Check for internal service headers (for service-to-service communication)
    internal_token = request.headers.get('X-Internal-Service-Token')
    expected_token = os.getenv('INTERNAL_SERVICE_TOKEN', 'alphintra-internal-token-2024')
    
    if internal_token and internal_token == expected_token:
        return True
    
    return False

def secure_microservice_endpoint(allowed_service_types=None):
    """
    Decorator for securing microservice endpoints
    
    Args:
        allowed_service_types: List of service types that can access this endpoint
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Validate internal request
            if not validate_internal_request():
                logger.warning(f"Unauthorized access attempt to {request.endpoint} from {request.remote_addr}")
                return jsonify({
                    'error': 'Unauthorized access',
                    'message': 'This endpoint can only be accessed through the API Gateway',
                    'status': 401
                }), 401
            
            # Check service type restrictions if specified
            if allowed_service_types:
                service_type = request.headers.get('X-Service-Type')
                if service_type not in allowed_service_types:
                    logger.warning(f"Service type {service_type} not allowed for {request.endpoint}")
                    return jsonify({
                        'error': 'Service type not allowed',
                        'message': f'Service type {service_type} is not authorized for this endpoint',
                        'status': 403
                    }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def add_security_headers(response):
    """
    Add security headers to microservice responses
    """
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Add service identification
    response.headers['X-Service-Response'] = 'alphintra-microservice'
    response.headers['X-Response-Source'] = os.getenv('SERVICE_NAME', 'unknown')
    
    return response

def init_microservice_security(app):
    """
    Initialize security for a microservice Flask app
    """
    # Add security headers to all responses
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response)
    
    # Add health check endpoint that bypasses security
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': os.getenv('SERVICE_NAME', 'unknown'),
            'timestamp': str(request.headers.get('X-Request-ID', 'unknown'))
        })
    
    # Add internal status endpoint for service-to-service communication
    @app.route('/internal/status')
    @secure_microservice_endpoint()
    def internal_status():
        return jsonify({
            'status': 'operational',
            'service': os.getenv('SERVICE_NAME', 'unknown'),
            'gateway_routed': request.headers.get('X-Gateway-Routed', 'false'),
            'request_id': request.headers.get('X-Request-ID', 'unknown')
        })
    
    logger.info(f"Microservice security initialized for {os.getenv('SERVICE_NAME', 'unknown')}")

# Configuration for different environments
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