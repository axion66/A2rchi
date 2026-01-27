"""
Unit tests for Authentication module.

Tests cover:
- AuthService (user CRUD, login, sessions)
- Auth decorators (@login_required, @admin_required)
- Auth routes (login, logout, user management)
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, PropertyMock
from flask import Flask, g, session

# Import auth module
from src.auth.service import AuthService, AuthenticationError
from src.auth.models import User
from src.auth.decorators import login_required, admin_required
from src.auth.routes import auth_bp, init_auth_routes, get_current_user


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_pg_config():
    """Mock PostgreSQL config."""
    return {
        'host': 'localhost',
        'port': 5432,
        'database': 'test',
        'user': 'user',
        'password': 'pass',
    }


@pytest.fixture
def sample_user_row():
    """Sample user row from database."""
    return {
        'id': 'user@example.com',
        'email': 'user@example.com',
        'display_name': 'Test User',
        'auth_provider': 'local',
        'password_hash': 'pbkdf2:sha256:...',
        'github_id': None,
        'github_username': None,
        'is_admin': False,
        'last_login_at': None,
        'login_count': 0,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
        'theme': 'light',
        'preferred_model': None,
        'preferred_temperature': None,
        'preferred_max_tokens': None,
        'preferred_num_documents': None,
        'preferred_condense_prompt': None,
        'preferred_chat_prompt': None,
        'preferred_system_prompt': None,
        'preferred_top_p': None,
        'preferred_top_k': None,
    }


@pytest.fixture
def flask_app():
    """Create Flask test app."""
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'
    app.config['TESTING'] = True
    return app


# =============================================================================
# User Model Tests
# =============================================================================

class TestUserModel:
    """Tests for User dataclass."""
    
    def test_from_db_row(self, sample_user_row):
        """Test creating User from database row."""
        user = User.from_db_row(sample_user_row)
        
        assert user.id == 'user@example.com'
        assert user.email == 'user@example.com'
        assert user.display_name == 'Test User'
        assert user.is_admin is False
        assert user.auth_provider == 'local'
    
    def test_from_db_row_none(self):
        """Test from_db_row with None returns None."""
        assert User.from_db_row(None) is None
    
    def test_flask_login_properties(self, sample_user_row):
        """Test Flask-Login compatibility properties."""
        user = User.from_db_row(sample_user_row)
        
        assert user.is_authenticated is True
        assert user.is_active is True
        assert user.is_anonymous is False
        assert user.get_id() == 'user@example.com'
    
    def test_to_dict_excludes_password(self, sample_user_row):
        """Test to_dict excludes password_hash."""
        user = User.from_db_row(sample_user_row)
        user_dict = user.to_dict()
        
        assert 'password_hash' not in user_dict
        assert 'email' in user_dict
        assert 'is_admin' in user_dict


# =============================================================================
# AuthService Tests
# =============================================================================

class TestAuthService:
    """Tests for AuthService."""
    
    def test_init(self, mock_pg_config):
        """Test AuthService initialization."""
        service = AuthService(mock_pg_config)
        assert service._pg_config == mock_pg_config
        assert service._session_lifetime_days == 30
    
    @patch('src.auth.service.psycopg2.connect')
    def test_get_user(self, mock_connect, mock_pg_config, sample_user_row):
        """Test getting user by ID."""
        # Setup mock cursor with context manager
        cursor = MagicMock()
        cursor.fetchone.return_value = sample_user_row
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        
        service = AuthService(mock_pg_config)
        user = service.get_user('user@example.com')
        
        assert user is not None
        assert user.email == 'user@example.com'
        cursor.execute.assert_called_once()
        conn.close.assert_called_once()
    
    @patch('src.auth.service.psycopg2.connect')
    def test_get_user_not_found(self, mock_connect, mock_pg_config):
        """Test getting non-existent user."""
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        
        service = AuthService(mock_pg_config)
        user = service.get_user('nonexistent@example.com')
        
        assert user is None
    
    @patch('src.auth.service.psycopg2.connect')
    @patch('src.auth.service.generate_password_hash')
    def test_create_user(self, mock_hash, mock_connect, mock_pg_config, sample_user_row):
        """Test creating a new user."""
        mock_hash.return_value = 'hashed_password'
        
        cursor = MagicMock()
        # First call for checking existing user returns None
        # Second call returns the created user
        cursor.fetchone.side_effect = [None, sample_user_row]
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        
        service = AuthService(mock_pg_config)
        user = service.create_user(
            email='newuser@example.com',
            password='password123',
            display_name='New User',
        )
        
        assert user is not None
        mock_hash.assert_called_once_with('password123')
        conn.commit.assert_called()
    
    @patch('src.auth.service.psycopg2.connect')
    def test_create_user_duplicate_email(self, mock_connect, mock_pg_config, sample_user_row):
        """Test creating user with existing email fails."""
        cursor = MagicMock()
        cursor.fetchone.return_value = sample_user_row  # User exists
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        
        service = AuthService(mock_pg_config)
        
        with pytest.raises(ValueError, match="already exists"):
            service.create_user(email='user@example.com', password='password')
    
    @patch('src.auth.service.psycopg2.connect')
    @patch('src.auth.service.check_password_hash')
    def test_login_success(self, mock_check, mock_connect, mock_pg_config, sample_user_row):
        """Test successful login."""
        mock_check.return_value = True
        
        cursor = MagicMock()
        cursor.fetchone.return_value = sample_user_row
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        
        service = AuthService(mock_pg_config)
        user, session_id = service.login('user@example.com', 'password123')
        
        assert user is not None
        assert session_id is not None
        assert len(session_id) > 20  # Token should be reasonably long
    
    @patch('src.auth.service.psycopg2.connect')
    def test_login_user_not_found(self, mock_connect, mock_pg_config):
        """Test login with non-existent user."""
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        
        service = AuthService(mock_pg_config)
        
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            service.login('nonexistent@example.com', 'password')
    
    @patch('src.auth.service.psycopg2.connect')
    @patch('src.auth.service.check_password_hash')
    def test_login_wrong_password(self, mock_check, mock_connect, mock_pg_config, sample_user_row):
        """Test login with wrong password."""
        mock_check.return_value = False
        
        cursor = MagicMock()
        cursor.fetchone.return_value = sample_user_row
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        
        service = AuthService(mock_pg_config)
        
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            service.login('user@example.com', 'wrongpassword')
    
    @patch('src.auth.service.psycopg2.connect')
    def test_create_session(self, mock_connect, mock_pg_config):
        """Test session creation."""
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        
        service = AuthService(mock_pg_config)
        session_id = service.create_session('user@example.com')
        
        assert session_id is not None
        assert len(session_id) > 20
        cursor.execute.assert_called_once()
        conn.commit.assert_called_once()
    
    @patch('src.auth.service.psycopg2.connect')
    def test_validate_session_valid(self, mock_connect, mock_pg_config, sample_user_row):
        """Test validating a valid session."""
        cursor = MagicMock()
        cursor.fetchone.return_value = sample_user_row
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        
        service = AuthService(mock_pg_config)
        user = service.validate_session('valid-session-id')
        
        assert user is not None
        assert user.email == 'user@example.com'
    
    @patch('src.auth.service.psycopg2.connect')
    def test_validate_session_expired(self, mock_connect, mock_pg_config):
        """Test validating an expired session."""
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        
        service = AuthService(mock_pg_config)
        user = service.validate_session('expired-session-id')
        
        assert user is None
    
    @patch('src.auth.service.psycopg2.connect')
    def test_logout(self, mock_connect, mock_pg_config):
        """Test logout deletes session."""
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        
        service = AuthService(mock_pg_config)
        service.logout('session-id')
        
        cursor.execute.assert_called_once()
        assert 'DELETE FROM sessions' in cursor.execute.call_args[0][0]
        conn.commit.assert_called_once()


# =============================================================================
# Decorator Tests
# =============================================================================

class TestDecorators:
    """Tests for auth decorators."""
    
    def test_login_required_authenticated(self, flask_app):
        """Test login_required allows authenticated users."""
        with flask_app.test_request_context():
            g.current_user = User(
                id='user@example.com',
                email='user@example.com',
                auth_provider='local',  # Not anonymous
                is_admin=False,
            )
            
            @login_required
            def protected_route():
                return {'status': 'ok'}
            
            result = protected_route()
            assert result == {'status': 'ok'}
    
    def test_login_required_anonymous(self, flask_app):
        """Test login_required rejects anonymous users."""
        with flask_app.test_request_context():
            g.current_user = None
            
            @login_required
            def protected_route():
                return {'status': 'ok'}
            
            response, status_code = protected_route()
            assert status_code == 401
    
    def test_admin_required_admin(self, flask_app):
        """Test admin_required allows admin users."""
        with flask_app.test_request_context():
            g.current_user = User(
                id='admin@example.com',
                email='admin@example.com',
                auth_provider='local',  # Not anonymous
                is_admin=True,
            )
            
            @admin_required
            def admin_route():
                return {'status': 'ok'}
            
            result = admin_route()
            assert result == {'status': 'ok'}
    
    def test_admin_required_non_admin(self, flask_app):
        """Test admin_required rejects non-admin users."""
        with flask_app.test_request_context():
            g.current_user = User(
                id='user@example.com',
                email='user@example.com',
                auth_provider='local',  # Not anonymous
                is_admin=False,
            )
            
            @admin_required
            def admin_route():
                return {'status': 'ok'}
            
            response, status_code = admin_route()
            assert status_code == 403


# =============================================================================
# Routes Tests
# =============================================================================

class TestAuthRoutes:
    """Tests for auth routes."""
    
    @pytest.fixture
    def mock_auth_service(self, sample_user_row):
        """Create mock AuthService."""
        service = MagicMock(spec=AuthService)
        service.login.return_value = (
            User.from_db_row(sample_user_row),
            'test-session-id'
        )
        service.validate_session.return_value = User.from_db_row(sample_user_row)
        service.list_users.return_value = [User.from_db_row(sample_user_row)]
        return service
    
    @pytest.fixture
    def client(self, flask_app, mock_auth_service):
        """Create test client with auth routes."""
        init_auth_routes(mock_auth_service)
        flask_app.register_blueprint(auth_bp)
        return flask_app.test_client()
    
    def test_login_success(self, client, mock_auth_service):
        """Test POST /auth/login with valid credentials."""
        response = client.post('/auth/login', json={
            'email': 'user@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Login successful'
        assert 'user' in data
        mock_auth_service.login.assert_called_once()
    
    def test_login_missing_fields(self, client):
        """Test POST /auth/login with missing fields."""
        response = client.post('/auth/login', json={
            'email': 'user@example.com'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_login_invalid_credentials(self, client, mock_auth_service):
        """Test POST /auth/login with invalid credentials."""
        mock_auth_service.login.side_effect = AuthenticationError("Invalid credentials")
        
        response = client.post('/auth/login', json={
            'email': 'user@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
    
    def test_logout(self, client, mock_auth_service):
        """Test POST /auth/logout."""
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session-id'
        
        response = client.post('/auth/logout')
        
        assert response.status_code == 200
        mock_auth_service.logout.assert_called_once_with('test-session-id')
    
    def test_get_me_authenticated(self, client, mock_auth_service, flask_app):
        """Test GET /auth/me when authenticated."""
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session-id'
        
        response = client.get('/auth/me')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['authenticated'] is True
        assert 'user' in data
    
    def test_get_me_anonymous(self, client, mock_auth_service):
        """Test GET /auth/me when not authenticated."""
        mock_auth_service.validate_session.return_value = None
        
        response = client.get('/auth/me')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['authenticated'] is False
        assert data['user'] is None


# =============================================================================
# Integration Tests (require PostgreSQL)
# =============================================================================

@pytest.mark.skipif(
    not pytest.importorskip("psycopg2", reason="psycopg2 not installed"),
    reason="PostgreSQL not available"
)
class TestAuthServiceIntegration:
    """Integration tests requiring real PostgreSQL.
    
    Run with: docker-compose up postgres (or use existing benchmark DB)
    Set env vars: PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
    """
    
    @pytest.fixture
    def pg_config(self):
        """Get PostgreSQL config from environment."""
        import os
        return {
            'host': os.environ.get('PG_HOST', 'localhost'),
            'port': int(os.environ.get('PG_PORT', 5433)),  # Default to benchmark port
            'database': os.environ.get('PG_DATABASE', 'benchmark'),
            'user': os.environ.get('PG_USER', 'benchmark'),
            'password': os.environ.get('PG_PASSWORD', 'benchmark'),
        }
    
    @pytest.fixture
    def auth_service_real(self, pg_config):
        """Create real AuthService."""
        return AuthService(pg_config)
    
    def test_full_auth_flow(self, auth_service_real):
        """Test complete auth flow: create user, login, session, logout."""
        import uuid
        test_email = f"test-{uuid.uuid4()}@example.com"
        
        try:
            # Create user
            user = auth_service_real.create_user(
                email=test_email,
                password='testpassword123',
                display_name='Test User',
            )
            assert user.email == test_email
            
            # Login
            user, session_id = auth_service_real.login(test_email, 'testpassword123')
            assert user.email == test_email
            assert session_id is not None
            
            # Validate session
            validated_user = auth_service_real.validate_session(session_id)
            assert validated_user is not None
            assert validated_user.email == test_email
            
            # Logout
            auth_service_real.logout(session_id)
            
            # Session should be invalid
            invalid_user = auth_service_real.validate_session(session_id)
            assert invalid_user is None
            
        finally:
            # Cleanup
            auth_service_real.delete_user(test_email)
