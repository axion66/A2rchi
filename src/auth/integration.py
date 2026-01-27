"""
Auth integration helpers for FlaskAppWrapper.

Provides functions to integrate the auth module into the Flask application.
"""

from typing import Any, Dict, Optional
from flask import Flask, g, session

from src.auth.service import AuthService
from src.auth.routes import auth_bp, init_auth_routes, get_current_user
from src.auth.github_oauth import create_github_oauth_client
from src.utils.env import read_secret
from src.utils.logging import get_logger

logger = get_logger(__name__)


def setup_auth(app: Flask, pg_config: Dict[str, Any]) -> AuthService:
    """
    Initialize and configure authentication for a Flask app.
    
    This sets up:
    1. AuthService with PostgreSQL connection
    2. Auth blueprint with routes
    3. GitHub OAuth client (if configured)
    4. Before request handler for current_user
    
    Args:
        app: Flask application
        pg_config: PostgreSQL connection configuration
        
    Returns:
        Configured AuthService instance
    """
    # Create AuthService
    auth_service = AuthService(pg_config)
    
    # Check for GitHub OAuth credentials
    github_client_id = read_secret('GITHUB_CLIENT_ID')
    github_client_secret = read_secret('GITHUB_CLIENT_SECRET')
    
    github_client = None
    if github_client_id and github_client_secret:
        github_client = create_github_oauth_client(
            app,
            client_id=github_client_id,
            client_secret=github_client_secret,
        )
        logger.info("GitHub OAuth client configured")
    else:
        logger.info("GitHub OAuth not configured (no GITHUB_CLIENT_ID/SECRET)")
    
    # Initialize routes with dependencies
    init_auth_routes(auth_service, github_client)
    
    # Register blueprint
    app.register_blueprint(auth_bp)
    logger.info("Auth blueprint registered at /auth/*")
    
    # Add before_request handler to populate g.current_user
    @app.before_request
    def load_current_user():
        """Load current user into Flask g for each request."""
        g.current_user = get_current_user()
        g.is_authenticated = g.current_user is not None
        g.is_admin = g.current_user.is_admin if g.current_user else False
    
    # Check for admin setup via environment variable
    admin_email = read_secret('ADMIN_EMAIL')
    admin_password = read_secret('ADMIN_PASSWORD')
    
    if admin_email:
        try:
            auth_service.ensure_admin(admin_email, admin_password)
            logger.info(f"Admin user ensured: {admin_email}")
        except Exception as e:
            logger.warning(f"Failed to ensure admin user: {e}")
    
    return auth_service


def get_user_id() -> str:
    """
    Get the current user ID for request context.
    
    Returns authenticated user ID, or generates anonymous ID.
    
    Returns:
        User ID string
    """
    user = getattr(g, 'current_user', None)
    if user and user.id:
        return user.id
    
    # Anonymous user - use session-based ID
    anon_id = session.get('anon_id')
    if not anon_id:
        import uuid
        anon_id = f"anon:{uuid.uuid4()}"
        session['anon_id'] = anon_id
    
    return anon_id


def is_authenticated() -> bool:
    """Check if current request is from authenticated user."""
    return getattr(g, 'is_authenticated', False)


def is_admin() -> bool:
    """Check if current request is from admin user."""
    return getattr(g, 'is_admin', False)
