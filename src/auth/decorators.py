"""
Authentication decorators for Flask routes.
"""

from functools import wraps
from typing import Callable

from flask import g, jsonify, request


def login_required(f: Callable) -> Callable:
    """
    Decorator requiring authenticated user (not anonymous).
    
    Returns 401 if user is not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'current_user', None)
        if user is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        if user.is_anonymous:
            return jsonify({'error': 'Authentication required'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f: Callable) -> Callable:
    """
    Decorator requiring admin user.
    
    Returns 401 if not authenticated, 403 if not admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'current_user', None)
        if user is None:
            return jsonify({'error': 'Authentication required'}), 401
        
        if user.is_anonymous:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
