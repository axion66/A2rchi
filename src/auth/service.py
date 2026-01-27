"""
AuthService - Core authentication service for A2rchi.

Handles user authentication, session management, and admin operations.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import psycopg2
import psycopg2.extras
from werkzeug.security import check_password_hash, generate_password_hash

from src.auth.models import User
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthService:
    """
    Service for managing user authentication and sessions.
    
    All sessions are stored in PostgreSQL.
    """
    
    DEFAULT_SESSION_LIFETIME_DAYS = 30
    
    def __init__(self, pg_config: Dict[str, Any]):
        """
        Initialize AuthService with PostgreSQL configuration.
        
        Args:
            pg_config: PostgreSQL connection parameters
        """
        self._pg_config = pg_config
        self._session_lifetime_days = self.DEFAULT_SESSION_LIFETIME_DAYS
    
    def _get_connection(self) -> psycopg2.extensions.connection:
        """Get a database connection."""
        return psycopg2.connect(**self._pg_config)
    
    # =========================================================================
    # User Operations
    # =========================================================================
    
    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                row = cursor.fetchone()
                return User.from_db_row(row) if row else None
        finally:
            conn.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                row = cursor.fetchone()
                return User.from_db_row(row) if row else None
        finally:
            conn.close()
    
    def get_user_by_github_id(self, github_id: str) -> Optional[User]:
        """
        Get user by GitHub ID.
        
        Args:
            github_id: GitHub user ID
            
        Returns:
            User if found, None otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE github_id = %s", (github_id,))
                row = cursor.fetchone()
                return User.from_db_row(row) if row else None
        finally:
            conn.close()
    
    def create_user(
        self,
        email: str,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        is_admin: bool = False,
        github_id: Optional[str] = None,
        github_username: Optional[str] = None,
    ) -> User:
        """
        Create a new user account.
        
        Args:
            email: User email (required)
            password: Password for local auth (optional)
            display_name: Display name
            is_admin: Whether user is admin
            github_id: GitHub user ID (for OAuth)
            github_username: GitHub username
            
        Returns:
            Created User
            
        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        existing = self.get_user_by_email(email)
        if existing:
            raise ValueError(f"User with email {email} already exists")
        
        # Generate user ID from email
        user_id = email.lower()
        
        # Hash password if provided
        password_hash = generate_password_hash(password) if password else None
        
        # Determine auth provider
        if github_id:
            auth_provider = 'github'
        elif password:
            auth_provider = 'local'
        else:
            auth_provider = 'anonymous'
        
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (
                        id, email, display_name, auth_provider, 
                        password_hash, github_id, github_username, is_admin
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (user_id, email, display_name or email.split('@')[0], auth_provider,
                     password_hash, github_id, github_username, is_admin)
                )
                row = cursor.fetchone()
                conn.commit()
                
                logger.info(f"Created user: {email} (admin={is_admin})")
                return User.from_db_row(row)
        except psycopg2.IntegrityError as e:
            conn.rollback()
            raise ValueError(f"User creation failed: {e}")
        finally:
            conn.close()
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        """
        Update user fields.
        
        Args:
            user_id: User ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated User, or None if not found
        """
        if not updates:
            return self.get_user(user_id)
        
        # Build SET clause
        allowed_fields = {
            'display_name', 'is_admin', 'theme', 'preferred_model',
            'preferred_temperature', 'preferred_max_tokens', 'preferred_num_documents',
            'preferred_condense_prompt', 'preferred_chat_prompt', 'preferred_system_prompt',
            'preferred_top_p', 'preferred_top_k', 'github_id', 'github_username'
        }
        
        set_parts = []
        values = []
        for key, value in updates.items():
            if key in allowed_fields:
                set_parts.append(f"{key} = %s")
                values.append(value)
        
        if not set_parts:
            return self.get_user(user_id)
        
        set_parts.append("updated_at = NOW()")
        values.append(user_id)
        
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    f"""
                    UPDATE users 
                    SET {', '.join(set_parts)}
                    WHERE id = %s
                    RETURNING *
                    """,
                    values
                )
                row = cursor.fetchone()
                conn.commit()
                return User.from_db_row(row) if row else None
        finally:
            conn.close()
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user and their sessions.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Sessions are deleted via CASCADE
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                deleted = cursor.rowcount > 0
                conn.commit()
                
                if deleted:
                    logger.info(f"Deleted user: {user_id}")
                
                return deleted
        finally:
            conn.close()
    
    def list_users(self, limit: int = 100, offset: int = 0) -> list:
        """
        List all users.
        
        Args:
            limit: Maximum number of users
            offset: Pagination offset
            
        Returns:
            List of User objects
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM users 
                    WHERE auth_provider != 'anonymous'
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset)
                )
                return [User.from_db_row(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def ensure_admin(self, email: str, password: Optional[str] = None) -> User:
        """
        Ensure a user with the given email exists and is an admin.
        
        Creates the user if they don't exist. If they exist, promotes to admin.
        
        Args:
            email: Admin email
            password: Password (only used if creating new user)
            
        Returns:
            Admin User
        """
        user = self.get_user_by_email(email)
        
        if user:
            if not user.is_admin:
                logger.info(f"Promoting existing user to admin: {email}")
                return self.update_user(user.id, {'is_admin': True})
            return user
        
        # Create new admin
        logger.info(f"Creating admin user: {email}")
        return self.create_user(
            email=email,
            password=password,
            is_admin=True,
        )
    
    # =========================================================================
    # Authentication
    # =========================================================================
    
    def login(self, email: str, password: str) -> Tuple[User, str]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (User, session_id)
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        user = self.get_user_by_email(email)
        
        if not user:
            logger.warning(f"Login failed: user not found - {email}")
            raise AuthenticationError("Invalid credentials")
        
        if not user.password_hash:
            logger.warning(f"Login failed: no password set - {email}")
            raise AuthenticationError("Invalid credentials")
        
        if not check_password_hash(user.password_hash, password):
            logger.warning(f"Login failed: wrong password - {email}")
            raise AuthenticationError("Invalid credentials")
        
        # Update login stats
        self._update_login_stats(user.id)
        
        # Create session
        session_id = self.create_session(user.id)
        
        logger.info(f"User logged in: {email}")
        return user, session_id
    
    def _update_login_stats(self, user_id: str) -> None:
        """Update user's login statistics."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users 
                    SET last_login_at = NOW(), login_count = login_count + 1
                    WHERE id = %s
                    """,
                    (user_id,)
                )
                conn.commit()
        finally:
            conn.close()
    
    # =========================================================================
    # Session Management
    # =========================================================================
    
    def create_session(self, user_id: str) -> str:
        """
        Create a new session for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self._session_lifetime_days)
        
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO sessions (id, user_id, expires_at)
                    VALUES (%s, %s, %s)
                    """,
                    (session_id, user_id, expires_at)
                )
                conn.commit()
                return session_id
        finally:
            conn.close()
    
    def validate_session(self, session_id: str) -> Optional[User]:
        """
        Validate session and return user if valid.
        
        Args:
            session_id: Session ID
            
        Returns:
            User if session valid, None if expired/invalid
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT u.* FROM sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.id = %s AND s.expires_at > NOW()
                    """,
                    (session_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    # Delete expired session if it exists
                    cursor.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
                    conn.commit()
                    return None
                
                return User.from_db_row(row)
        finally:
            conn.close()
    
    def logout(self, session_id: str) -> None:
        """
        Delete a session (logout).
        
        Args:
            session_id: Session ID
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
                conn.commit()
        finally:
            conn.close()
    
    def cleanup_expired_sessions(self) -> int:
        """
        Delete all expired sessions.
        
        Returns:
            Number of sessions deleted
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM sessions WHERE expires_at < NOW()")
                deleted = cursor.rowcount
                conn.commit()
                
                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} expired sessions")
                
                return deleted
        finally:
            conn.close()
    
    # =========================================================================
    # GitHub OAuth
    # =========================================================================
    
    def github_callback(
        self, 
        github_id: str, 
        email: str, 
        username: str
    ) -> Tuple[User, str]:
        """
        Handle GitHub OAuth callback.
        
        Finds user by github_id or email (auto-link), or rejects if no match.
        
        Args:
            github_id: GitHub user ID
            email: GitHub email
            username: GitHub username
            
        Returns:
            Tuple of (User, session_id)
            
        Raises:
            AuthenticationError: If no matching user found
        """
        # Try to find by GitHub ID first
        user = self.get_user_by_github_id(github_id)
        
        if not user:
            # Try to find by email (auto-link)
            user = self.get_user_by_email(email)
            
            if user:
                # Auto-link GitHub account
                logger.info(f"Auto-linking GitHub account for: {email}")
                user = self.update_user(user.id, {
                    'github_id': github_id,
                    'github_username': username,
                })
            else:
                # No user found - must be created by admin first
                logger.warning(f"GitHub login failed: no account for {email}")
                raise AuthenticationError(
                    "Account not found. Please contact an administrator to create your account."
                )
        
        # Update login stats
        self._update_login_stats(user.id)
        
        # Create session
        session_id = self.create_session(user.id)
        
        logger.info(f"User logged in via GitHub: {email}")
        return user, session_id
