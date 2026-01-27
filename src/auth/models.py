"""
User model for Flask-Login integration.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    User model representing an authenticated user.
    
    Compatible with Flask-Login's UserMixin requirements.
    """
    
    id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    auth_provider: str = 'anonymous'
    
    # Auth fields
    password_hash: Optional[str] = None
    github_id: Optional[str] = None
    github_username: Optional[str] = None
    
    # Role
    is_admin: bool = False
    
    # Preferences
    theme: str = 'system'
    preferred_model: Optional[str] = None
    preferred_temperature: Optional[float] = None
    preferred_max_tokens: Optional[int] = None
    preferred_num_documents: Optional[int] = None
    preferred_condense_prompt: Optional[str] = None
    preferred_chat_prompt: Optional[str] = None
    preferred_system_prompt: Optional[str] = None
    preferred_top_p: Optional[float] = None
    preferred_top_k: Optional[int] = None
    
    # BYOK keys (encrypted, stored as bytes)
    api_key_openrouter: Optional[bytes] = None
    api_key_openai: Optional[bytes] = None
    api_key_anthropic: Optional[bytes] = None
    
    # Timestamps
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Flask-Login required properties
    @property
    def is_authenticated(self) -> bool:
        """Return True if user is authenticated (not anonymous)."""
        return self.auth_provider != 'anonymous'
    
    @property
    def is_active(self) -> bool:
        """Return True if user is active."""
        return True
    
    @property
    def is_anonymous(self) -> bool:
        """Return True if user is anonymous."""
        return self.auth_provider == 'anonymous'
    
    def get_id(self) -> str:
        """Return user ID as string (required by Flask-Login)."""
        return self.id
    
    @classmethod
    def from_db_row(cls, row: dict) -> 'User':
        """Create User from database row dictionary."""
        if row is None:
            return None
        return cls(
            id=row['id'],
            email=row.get('email'),
            display_name=row.get('display_name'),
            auth_provider=row.get('auth_provider', 'anonymous'),
            password_hash=row.get('password_hash'),
            github_id=row.get('github_id'),
            github_username=row.get('github_username'),
            is_admin=row.get('is_admin', False),
            theme=row.get('theme', 'system'),
            preferred_model=row.get('preferred_model'),
            preferred_temperature=float(row['preferred_temperature']) if row.get('preferred_temperature') else None,
            preferred_max_tokens=row.get('preferred_max_tokens'),
            preferred_num_documents=row.get('preferred_num_documents'),
            preferred_condense_prompt=row.get('preferred_condense_prompt'),
            preferred_chat_prompt=row.get('preferred_chat_prompt'),
            preferred_system_prompt=row.get('preferred_system_prompt'),
            preferred_top_p=float(row['preferred_top_p']) if row.get('preferred_top_p') else None,
            preferred_top_k=row.get('preferred_top_k'),
            api_key_openrouter=row.get('api_key_openrouter'),
            api_key_openai=row.get('api_key_openai'),
            api_key_anthropic=row.get('api_key_anthropic'),
            last_login_at=row.get('last_login_at'),
            login_count=row.get('login_count', 0),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert to dictionary for JSON serialization.
        
        Args:
            include_sensitive: If True, include password_hash and API keys
        """
        data = {
            'id': self.id,
            'email': self.email,
            'display_name': self.display_name,
            'auth_provider': self.auth_provider,
            'github_username': self.github_username,
            'is_admin': self.is_admin,
            'theme': self.theme,
            'preferred_model': self.preferred_model,
            'preferred_temperature': self.preferred_temperature,
            'preferred_max_tokens': self.preferred_max_tokens,
            'preferred_num_documents': self.preferred_num_documents,
            'preferred_condense_prompt': self.preferred_condense_prompt,
            'preferred_chat_prompt': self.preferred_chat_prompt,
            'preferred_system_prompt': self.preferred_system_prompt,
            'preferred_top_p': self.preferred_top_p,
            'preferred_top_k': self.preferred_top_k,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            data['has_openrouter_key'] = self.api_key_openrouter is not None
            data['has_openai_key'] = self.api_key_openai is not None
            data['has_anthropic_key'] = self.api_key_anthropic is not None
        
        return data
