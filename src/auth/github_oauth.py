"""
GitHub OAuth client configuration.

Configures Authlib OAuth client for GitHub authentication.
"""

from typing import Optional
from authlib.integrations.flask_client import OAuth

from src.utils.logging import get_logger

logger = get_logger(__name__)


def create_github_oauth_client(
    app,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> Optional[OAuth]:
    """
    Create and configure GitHub OAuth client.
    
    Args:
        app: Flask application
        client_id: GitHub OAuth App client ID
        client_secret: GitHub OAuth App client secret
        
    Returns:
        Configured OAuth instance, or None if credentials missing
    """
    if not client_id or not client_secret:
        logger.info("GitHub OAuth not configured (missing client_id or client_secret)")
        return None
    
    oauth = OAuth(app)
    
    oauth.register(
        name='github',
        client_id=client_id,
        client_secret=client_secret,
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        api_base_url='https://api.github.com/',
        client_kwargs={
            'scope': 'user:email read:user',
        },
    )
    
    logger.info("GitHub OAuth client configured")
    return oauth.github
