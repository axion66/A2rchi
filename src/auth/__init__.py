"""
A2rchi Authentication Module

Provides user authentication via local accounts and GitHub OAuth,
with session management stored in PostgreSQL.
"""

from src.auth.service import AuthService, AuthenticationError
from src.auth.decorators import login_required, admin_required
from src.auth.models import User
from src.auth.routes import auth_bp, init_auth_routes, get_current_user
from src.auth.github_oauth import create_github_oauth_client
from src.auth.integration import setup_auth, get_user_id, is_authenticated, is_admin

__all__ = [
    # Core
    'AuthService',
    'AuthenticationError',
    'User',
    # Decorators
    'login_required',
    'admin_required',
    # Routes
    'auth_bp',
    'init_auth_routes',
    'get_current_user',
    # OAuth
    'create_github_oauth_client',
    # Integration helpers
    'setup_auth',
    'get_user_id',
    'is_authenticated',
    'is_admin',
]
