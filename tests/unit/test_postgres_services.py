"""
Unit tests for PostgreSQL services.

Tests cover:
- ConnectionPool
- UserService  
- ConfigService
- DocumentSelectionService
- ConversationService
- PostgresServiceFactory
"""
import os
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

# Import services
from src.utils.connection_pool import ConnectionPool, ConnectionPoolError, ConnectionTimeoutError
from src.utils.user_service import UserService, User
from src.utils.config_service import ConfigService, StaticConfig, DynamicConfig, ConfigValidationError
from src.utils.document_selection_service import DocumentSelectionService, DocumentSelection
from src.utils.conversation_service import ConversationService, Message, ABComparison
from src.utils.postgres_service_factory import PostgresServiceFactory, create_services


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_connection():
    """Create a mock psycopg2 connection."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cursor


@pytest.fixture
def mock_pool(mock_connection):
    """Create a mock connection pool."""
    conn, cursor = mock_connection
    pool = MagicMock(spec=ConnectionPool)
    pool.get_connection.return_value = conn
    return pool


# =============================================================================
# ConnectionPool Tests
# =============================================================================

class TestConnectionPool:
    """Tests for ConnectionPool."""
    
    def test_init_requires_params_or_dsn(self):
        """Test that ConnectionPool requires connection info."""
        with pytest.raises(ValueError, match="Either pg_config or connection_params must be provided"):
            ConnectionPool()
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_init_with_params(self, mock_tcp):
        """Test initialization with connection params."""
        params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'test',
            'user': 'user',
            'password': 'pass',
        }
        pool = ConnectionPool(connection_params=params)
        
        mock_tcp.assert_called_once()
        assert pool._pool is not None
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_singleton_pattern(self, mock_tcp):
        """Test singleton pattern."""
        params = {'host': 'localhost', 'database': 'test', 'user': 'user', 'password': 'pass'}
        
        # Reset singleton
        ConnectionPool._instance = None
        
        pool1 = ConnectionPool.get_instance(connection_params=params)
        pool2 = ConnectionPool.get_instance()
        
        assert pool1 is pool2


# =============================================================================
# UserService Tests
# =============================================================================

class TestUserService:
    """Tests for UserService."""
    
    def test_get_or_create_user_creates_new(self, mock_pool, mock_connection):
        """Test creating a new user."""
        conn, cursor = mock_connection
        cursor.fetchone.return_value = None  # User doesn't exist
        
        service = UserService(connection_pool=mock_pool, encryption_key="test-key")
        user = service.get_or_create_user("user123", auth_provider="anonymous")
        
        assert user.id == "user123"
        assert user.auth_provider == "anonymous"
    
    def test_get_or_create_user_returns_existing(self, mock_pool, mock_connection):
        """Test returning existing user."""
        conn, cursor = mock_connection
        # Simulate existing user
        cursor.fetchone.return_value = (
            "user123", "Test User", "test@example.com", "basic",
            "dark", "gpt-4", 0.7,
            None, None, None,  # API keys
            datetime.now(), datetime.now()
        )
        
        service = UserService(connection_pool=mock_pool, encryption_key="test-key")
        user = service.get_or_create_user("user123")
        
        assert user.id == "user123"
        assert user.display_name == "Test User"
        assert user.theme == "dark"
    
    def test_update_preferences(self, mock_pool, mock_connection):
        """Test updating user preferences."""
        conn, cursor = mock_connection
        cursor.fetchone.return_value = (
            "user123", "Updated Name", None, "anonymous",
            "light", "gpt-4o", 0.5,
            None, None, None,
            datetime.now(), datetime.now()
        )
        
        service = UserService(connection_pool=mock_pool, encryption_key="test-key")
        user = service.update_preferences(
            user_id="user123",
            display_name="Updated Name",
            theme="light",
        )
        
        assert user.display_name == "Updated Name"
        assert user.theme == "light"


# =============================================================================
# ConfigService Tests
# =============================================================================

class TestConfigService:
    """Tests for ConfigService."""
    
    def test_get_static_config(self, mock_pool, mock_connection):
        """Test getting static config."""
        conn, cursor = mock_connection
        cursor.fetchone.return_value = (
            "test-deployment", "2.0.0", "/data",
            "text-embedding-ada-002", 1536, 1000, 150, "cosine",
            ["QAPipeline"], ["gpt-4"], ["openai"],
            False, datetime.now()
        )
        
        service = ConfigService(connection_pool=mock_pool)
        config = service.get_static_config()
        
        assert config.deployment_name == "test-deployment"
        assert config.embedding_dimensions == 1536
        assert "QAPipeline" in config.available_pipelines
    
    def test_get_static_config_caching(self, mock_pool, mock_connection):
        """Test that static config is cached."""
        conn, cursor = mock_connection
        cursor.fetchone.return_value = (
            "test", "2.0.0", "/data",
            "model", 384, 1000, 150, "cosine",
            [], [], [], False, datetime.now()
        )
        
        service = ConfigService(connection_pool=mock_pool)
        
        # First call
        config1 = service.get_static_config()
        # Second call should use cache
        config2 = service.get_static_config()
        
        assert config1 is config2
        # Only one DB call
        assert mock_pool.get_connection.call_count == 1
    
    def test_update_dynamic_config_validation(self, mock_pool, mock_connection):
        """Test dynamic config validation."""
        conn, cursor = mock_connection
        
        service = ConfigService(connection_pool=mock_pool)
        
        with pytest.raises(ConfigValidationError, match="Temperature"):
            service.update_dynamic_config(temperature=5.0)
        
        with pytest.raises(ConfigValidationError, match="max_tokens"):
            service.update_dynamic_config(max_tokens=-1)


# =============================================================================
# DocumentSelectionService Tests
# =============================================================================

class TestDocumentSelectionService:
    """Tests for DocumentSelectionService."""
    
    def test_get_enabled_document_ids(self, mock_pool, mock_connection):
        """Test getting enabled document IDs."""
        conn, cursor = mock_connection
        cursor.fetchall.return_value = [(1,), (2,), (5,)]
        
        service = DocumentSelectionService(connection_pool=mock_pool)
        doc_ids = service.get_enabled_document_ids(
            user_id="user123",
            conversation_id=42,
        )
        
        assert doc_ids == [1, 2, 5]
    
    def test_set_user_default(self, mock_pool, mock_connection):
        """Test setting user default."""
        conn, cursor = mock_connection
        
        service = DocumentSelectionService(connection_pool=mock_pool)
        service.set_user_default(
            user_id="user123",
            document_id=10,
            enabled=False,
        )
        
        # Verify UPSERT was called
        conn.commit.assert_called()
    
    def test_3tier_precedence_query(self, mock_pool, mock_connection):
        """Test that the 3-tier precedence is in the query."""
        conn, cursor = mock_connection
        cursor.fetchall.return_value = []
        
        service = DocumentSelectionService(connection_pool=mock_pool)
        service.get_enabled_document_ids("user", 1)
        
        # Check that the query includes COALESCE for precedence
        call_args = cursor.execute.call_args
        query = call_args[0][0]
        assert "COALESCE" in query


# =============================================================================
# ConversationService Tests
# =============================================================================

class TestConversationService:
    """Tests for ConversationService."""
    
    def test_insert_message(self, mock_pool, mock_connection):
        """Test inserting a message."""
        conn, cursor = mock_connection
        
        # Mock execute_values return
        with patch('src.utils.conversation_service.execute_values') as mock_exec:
            mock_exec.return_value = None
            cursor.fetchall.return_value = [(1,)]
            mock_exec.return_value = [(1,)]
            
            service = ConversationService(connection_pool=mock_pool)
            
            msg = Message(
                conversation_id="conv123",
                sender="user",
                content="Hello",
                model_used="gpt-4",
                pipeline_used="QAPipeline",
            )
            
            # The service calls execute_values which returns IDs
            with patch.object(service, 'insert_messages', return_value=[1]):
                msg_id = service.insert_message(msg)
                assert msg_id == 1
    
    def test_create_ab_comparison(self, mock_pool, mock_connection):
        """Test creating A/B comparison."""
        conn, cursor = mock_connection
        cursor.fetchone.return_value = (42,)  # comparison_id
        
        service = ConversationService(connection_pool=mock_pool)
        comparison_id = service.create_ab_comparison(
            conversation_id="conv123",
            user_prompt_mid=1,
            response_a_mid=2,
            response_b_mid=3,
            model_a="gpt-4",
            pipeline_a="QAPipeline",
            model_b="claude-3",
            pipeline_b="QAPipeline",
        )
        
        assert comparison_id == 42
    
    def test_record_ab_preference_validation(self, mock_pool, mock_connection):
        """Test preference validation."""
        service = ConversationService(connection_pool=mock_pool)
        
        with pytest.raises(ValueError, match="Invalid preference"):
            service.record_ab_preference(1, "invalid")


# =============================================================================
# PostgresServiceFactory Tests
# =============================================================================

class TestPostgresServiceFactory:
    """Tests for PostgresServiceFactory."""
    
    @patch('src.utils.postgres_service_factory.ConnectionPool')
    def test_from_config(self, mock_pool_class):
        """Test factory creation from config."""
        factory = PostgresServiceFactory.from_config(
            connection_params={
                'host': 'localhost',
                'database': 'test',
                'user': 'user',
                'password': 'pass',
            }
        )
        
        assert factory is not None
        mock_pool_class.assert_called_once()
    
    @patch('src.utils.postgres_service_factory.ConnectionPool')
    def test_lazy_service_initialization(self, mock_pool_class):
        """Test that services are lazy-initialized."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        factory = PostgresServiceFactory.from_config(
            connection_params={'host': 'localhost', 'database': 'test', 'user': 'u', 'password': 'p'}
        )
        
        # Services should not be created yet
        assert factory._user_service is None
        assert factory._config_service is None
        
        # Access services
        _ = factory.user_service
        _ = factory.config_service
        
        # Now they should exist
        assert factory._user_service is not None
        assert factory._config_service is not None
    
    @patch('src.utils.postgres_service_factory.ConnectionPool')
    def test_context_manager(self, mock_pool_class):
        """Test context manager cleanup."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        with PostgresServiceFactory.from_config(
            connection_params={'host': 'localhost', 'database': 'test', 'user': 'u', 'password': 'p'}
        ) as factory:
            _ = factory.user_service
        
        # Pool should be closed
        mock_pool.close.assert_called_once()
    
    def test_from_yaml_config(self):
        """Test factory creation from YAML config structure."""
        config = {
            'database': {
                'postgres': {
                    'host': 'db.example.com',
                    'port': 5433,
                    'database': 'a2rchi',
                    'user': 'app',
                    'password': 'secret',
                    'pool': {
                        'min_connections': 2,
                        'max_connections': 10,
                    }
                }
            }
        }
        
        with patch('src.utils.postgres_service_factory.ConnectionPool') as mock_pool_class:
            factory = PostgresServiceFactory.from_yaml_config(config)
            
            # Verify connection params were extracted correctly
            call_kwargs = mock_pool_class.call_args[1]
            assert call_kwargs['connection_params']['host'] == 'db.example.com'
            assert call_kwargs['connection_params']['port'] == 5433
            assert call_kwargs['min_connections'] == 2
            assert call_kwargs['max_connections'] == 10


# =============================================================================
# Integration-style Tests (with mocked DB)
# =============================================================================

class TestServiceIntegration:
    """Integration tests for service interactions."""
    
    @patch('src.utils.postgres_service_factory.ConnectionPool')
    def test_user_document_selection_flow(self, mock_pool_class):
        """Test user setting document defaults."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_pool.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool_class.return_value = mock_pool
        
        factory = PostgresServiceFactory.from_config(
            connection_params={'host': 'localhost', 'database': 'test', 'user': 'u', 'password': 'p'}
        )
        
        # Set user document default
        factory.document_selection_service.set_user_default(
            user_id="user123",
            document_id=10,
            enabled=False,
        )
        
        # Verify commit was called
        mock_conn.commit.assert_called()


# =============================================================================
# Message/ABComparison Dataclass Tests
# =============================================================================

class TestDataclasses:
    """Tests for dataclass structures."""
    
    def test_message_defaults(self):
        """Test Message default values."""
        msg = Message()
        
        assert msg.message_id is None
        assert msg.conversation_id == ""
        assert msg.sender == ""
        assert msg.a2rchi_service == "chat"
    
    def test_ab_comparison_defaults(self):
        """Test ABComparison default values."""
        ab = ABComparison()
        
        assert ab.comparison_id is None
        assert ab.is_config_a_first is True
        assert ab.preference is None
    
    def test_document_selection_repr(self):
        """Test DocumentSelection representation."""
        ds = DocumentSelection(
            document_id=1,
            user_default=False,
            conversation_override=True,
            effective_enabled=True,
        )
        
        assert ds.document_id == 1
        assert ds.effective_enabled is True
