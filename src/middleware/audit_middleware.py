"""
Flask middleware for automatic audit logging.
"""

import logging
from flask import request, g
from functools import wraps
from typing import Callable
from src.logging_conf import audit_logger


logger = logging.getLogger(__name__)


def get_user_id() -> str:
    """
    Extract user ID from request.
    
    You can customize this based on your auth mechanism:
    - Session cookie
    - JWT token
    - API key
    - etc.
    """
    # For now, use session ID or IP address
    if hasattr(g, 'user_id'):
        return g.user_id
    
    # Fallback to session or IP
    from flask import session
    if 'user_id' in session:
        return session['user_id']
    
    return request.remote_addr or "unknown"


def audit_endpoint(action: str):
    """
    Decorator for endpoints that should be audited.
    
    Usage:
        @app.route('/api/deck/import', methods=['POST'])
        @audit_endpoint('import_deck')
        def import_deck():
            ...
    
    Args:
        action: Human-readable action name
    """
    def decorator(f: Callable):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = get_user_id()
            
            # Log the request
            logger.debug(
                f"User {user_id} calling {request.endpoint} "
                f"({request.method} {request.path})"
            )
            
            # Call the actual endpoint
            response = f(*args, **kwargs)
            
            # Extract status code
            if isinstance(response, tuple):
                status_code = response[1] if len(response) > 1 else 200
            else:
                status_code = 200
            
            # Get request details
            details = {
                "path": request.path,
                "args": dict(request.args),
            }
            
            # Add body for POST/PUT (be careful with sensitive data!)
            if request.method in ['POST', 'PUT', 'PATCH']:
                if request.is_json:
                    # Don't log sensitive fields
                    body = request.get_json()
                    if body and isinstance(body, dict):
                        # Filter out sensitive keys
                        filtered_body = {
                            k: v for k, v in body.items() 
                            if k not in ['password', 'token', 'secret', 'cookie']
                        }
                        details["body"] = filtered_body
            
            # Log to audit log
            audit_logger.log_action(
                action=action,
                user_id=user_id,
                endpoint=request.endpoint,
                method=request.method,
                status_code=status_code,
                details=details
            )
            
            logger.info(
                f"Action '{action}' completed for user {user_id} "
                f"(status: {status_code})"
            )
            
            return response
        
        return wrapper
    return decorator


def setup_request_logging(app):
    """
    Add request/response logging to Flask app.
    
    Call this in app.py after creating the Flask app.
    """
    @app.before_request
    def log_request():
        logger.debug(f">> {request.method} {request.path}")
    
    @app.after_request
    def log_response(response):
        logger.debug(f"<< {response.status_code} {request.path}")
        return response
