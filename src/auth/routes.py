"""
Authentication routes Flask Blueprint.

Provides REST API endpoints for authentication:
- POST /auth/login     - Local login with email/password
- POST /auth/logout    - End session
- GET  /auth/me        - Get current user
- GET  /auth/github    - Start GitHub OAuth
- GET  /auth/callback  - GitHub OAuth callback
"""

from functools import wraps
from typing import Any, Dict, Optional

from flask import Blueprint, g, jsonify, redirect, request, session, url_for

from src.auth.service import AuthService, AuthenticationError
from src.auth.models import User
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Will be set by init_auth_routes()
_auth_service: Optional[AuthService] = None
_github_client = None

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def init_auth_routes(auth_service: AuthService, github_client=None):
    """
    Initialize auth routes with dependencies.
    
    Args:
        auth_service: AuthService instance
        github_client: Optional Authlib OAuth client for GitHub
    """
    global _auth_service, _github_client
    _auth_service = auth_service
    _github_client = github_client


def get_current_user() -> Optional[User]:
    """
    Get the current user from the request session.
    
    Returns:
        User if authenticated, None otherwise
    """
    if hasattr(g, 'current_user'):
        return g.current_user
    
    # Check session
    session_id = session.get('session_id')
    if not session_id:
        g.current_user = None
        return None
    
    user = _auth_service.validate_session(session_id)
    g.current_user = user
    return user


# =============================================================================
# Local Authentication Routes
# =============================================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login with email and password.
    
    Request body:
        {
            "email": "user@example.com",
            "password": "password123"
        }
    
    Response (200):
        {
            "user": {...user object...},
            "message": "Login successful"
        }
    
    Response (401):
        {
            "error": "Invalid credentials"
        }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    try:
        user, session_id = _auth_service.login(email, password)
        
        # Store session in Flask session
        session['session_id'] = session_id
        session.permanent = True
        
        return jsonify({
            'user': user.to_dict(),
            'message': 'Login successful'
        }), 200
        
    except AuthenticationError as e:
        return jsonify({'error': str(e)}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    End the current session.
    
    Response (200):
        {
            "message": "Logged out"
        }
    """
    session_id = session.get('session_id')
    
    if session_id:
        _auth_service.logout(session_id)
        session.pop('session_id', None)
    
    return jsonify({'message': 'Logged out'}), 200


@auth_bp.route('/me', methods=['GET'])
def get_me():
    """
    Get the current authenticated user.
    
    Response (200) - Authenticated:
        {
            "user": {...user object...},
            "authenticated": true
        }
    
    Response (200) - Anonymous:
        {
            "user": null,
            "authenticated": false
        }
    """
    user = get_current_user()
    
    if user:
        return jsonify({
            'user': user.to_dict(),
            'authenticated': True
        }), 200
    else:
        return jsonify({
            'user': None,
            'authenticated': False
        }), 200


# =============================================================================
# Admin User Management Routes
# =============================================================================

@auth_bp.route('/users', methods=['GET'])
def list_users():
    """
    List all users (admin only).
    
    Response (200):
        {
            "users": [...user objects...]
        }
    
    Response (403):
        {
            "error": "Admin access required"
        }
    """
    user = get_current_user()
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    users = _auth_service.list_users(limit=limit, offset=offset)
    
    return jsonify({
        'users': [u.to_dict() for u in users]
    }), 200


@auth_bp.route('/users', methods=['POST'])
def create_user():
    """
    Create a new user (admin only).
    
    Request body:
        {
            "email": "newuser@example.com",
            "password": "optional",
            "display_name": "New User",
            "is_admin": false
        }
    
    Response (201):
        {
            "user": {...user object...},
            "message": "User created"
        }
    """
    user = get_current_user()
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({'error': 'Email required'}), 400
    
    try:
        new_user = _auth_service.create_user(
            email=data['email'],
            password=data.get('password'),
            display_name=data.get('display_name'),
            is_admin=data.get('is_admin', False),
        )
        
        return jsonify({
            'user': new_user.to_dict(),
            'message': 'User created'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@auth_bp.route('/users/<user_id>', methods=['PATCH'])
def update_user(user_id: str):
    """
    Update a user (admin only, or self).
    
    Request body:
        {
            "display_name": "New Name",
            "is_admin": true,
            ...
        }
    """
    current_user = get_current_user()
    
    # Allow self-update for non-admin fields
    is_self = current_user and current_user.id == user_id
    is_admin = current_user and current_user.is_admin
    
    if not is_self and not is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    # Non-admins can't promote to admin
    if not is_admin and data.get('is_admin'):
        return jsonify({'error': 'Cannot set admin status'}), 403
    
    updated_user = _auth_service.update_user(user_id, data)
    
    if not updated_user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': updated_user.to_dict(),
        'message': 'User updated'
    }), 200


@auth_bp.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id: str):
    """
    Delete a user (admin only).
    """
    user = get_current_user()
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Prevent self-deletion
    if user.id == user_id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    if _auth_service.delete_user(user_id):
        return jsonify({'message': 'User deleted'}), 200
    else:
        return jsonify({'error': 'User not found'}), 404


# =============================================================================
# GitHub OAuth Routes
# =============================================================================

@auth_bp.route('/github', methods=['GET'])
def github_login():
    """
    Start GitHub OAuth flow.
    
    Redirects to GitHub authorization page.
    """
    if not _github_client:
        return jsonify({'error': 'GitHub OAuth not configured'}), 501
    
    redirect_uri = url_for('auth.github_callback', _external=True)
    return _github_client.authorize_redirect(redirect_uri)


@auth_bp.route('/callback', methods=['GET'])
def github_callback():
    """
    Handle GitHub OAuth callback.
    
    On success, creates/updates session and redirects to app.
    On failure, redirects to login with error.
    """
    if not _github_client:
        return jsonify({'error': 'GitHub OAuth not configured'}), 501
    
    try:
        token = _github_client.authorize_access_token()
        
        # Get user info from GitHub
        resp = _github_client.get('user', token=token)
        github_user = resp.json()
        
        # Get email (might require additional API call)
        github_id = str(github_user['id'])
        username = github_user['login']
        email = github_user.get('email')
        
        if not email:
            # Email not public, fetch from emails API
            emails_resp = _github_client.get('user/emails', token=token)
            emails = emails_resp.json()
            
            # Find primary email
            for e in emails:
                if e.get('primary'):
                    email = e['email']
                    break
            
            if not email:
                return redirect('/login?error=no_email')
        
        # Auth with service
        user, session_id = _auth_service.github_callback(
            github_id=github_id,
            email=email,
            username=username
        )
        
        # Store session
        session['session_id'] = session_id
        session.permanent = True
        
        # Redirect to app
        return redirect('/')
        
    except AuthenticationError as e:
        logger.warning(f"GitHub OAuth failed: {e}")
        return redirect(f'/login?error=account_not_found')
    except Exception as e:
        logger.error(f"GitHub OAuth error: {e}")
        return redirect('/login?error=oauth_failed')
