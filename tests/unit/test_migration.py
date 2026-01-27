"""
Unit tests for MigrationManager.

Tests cover:
- Migration analysis (dry run)
- ChromaDB → PostgreSQL migration
- SQLite catalog → PostgreSQL migration
- Conversation schema migration
- Configs table cleanup
- Checkpoint and resume functionality
"""
import json
import os
import pytest
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch, call

from src.utils.migration_manager import (
    MigrationManager,
    MigrationCheckpoint,
    MigrationStatus,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_pg_connection():
    """Create a mock PostgreSQL connection."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cursor


@pytest.fixture
def pg_params():
    """Standard PostgreSQL connection params."""
    return {
        'host': 'localhost',
        'port': 5432,
        'database': 'a2rchi_test',
        'user': 'postgres',
        'password': 'testpass',
    }


@pytest.fixture
def migration_manager(pg_params):
    """Create MigrationManager with mocked connection."""
    with patch.object(MigrationManager, '_get_pg_connection'):
        manager = MigrationManager(
            postgres_conn_params=pg_params,
            chroma_path=None,
            sqlite_path=None,
        )
        return manager


# =============================================================================
# MigrationManager Initialization Tests
# =============================================================================

class TestMigrationManagerInit:
    """Tests for MigrationManager initialization."""
    
    def test_init_with_params(self, pg_params):
        """Test initialization with postgres params."""
        with patch.object(MigrationManager, '_get_pg_connection'):
            manager = MigrationManager(postgres_conn_params=pg_params)
            assert manager._pg_params == pg_params
    
    def test_init_with_pg_config_alias(self, pg_params):
        """Test initialization with pg_config alias."""
        with patch.object(MigrationManager, '_get_pg_connection'):
            manager = MigrationManager(pg_config=pg_params)
            assert manager._pg_params == pg_params
    
    def test_init_with_chroma_path(self, pg_params):
        """Test initialization with ChromaDB path."""
        with patch.object(MigrationManager, '_get_pg_connection'):
            manager = MigrationManager(
                postgres_conn_params=pg_params,
                chroma_path="/path/to/chroma",
            )
            assert manager._chroma_path == "/path/to/chroma"
    
    def test_init_with_chromadb_path_alias(self, pg_params):
        """Test initialization with chromadb_path alias."""
        with patch.object(MigrationManager, '_get_pg_connection'):
            manager = MigrationManager(
                pg_config=pg_params,
                chromadb_path="/path/to/chroma",
            )
            assert manager._chroma_path == "/path/to/chroma"


# =============================================================================
# Migration Analysis Tests
# =============================================================================

class TestMigrationAnalysis:
    """Tests for migration analysis (dry run)."""
    
    def test_analyze_empty_sources(self, migration_manager, mock_pg_connection):
        """Test analysis with no source data."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.return_value = (0,)  # No conversations to update
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            result = migration_manager.analyze_migration()
        
        assert result['chromadb_count'] == 0
        assert result['sqlite_count'] == 0
        assert result['conversations_count'] == 0
    
    def test_analyze_with_chromadb(self, pg_params, mock_pg_connection):
        """Test analysis with ChromaDB data."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.return_value = (100,)
        
        with patch.object(MigrationManager, '_get_pg_connection', return_value=conn):
            with patch('src.utils.migration_manager.chromadb') as mock_chromadb:
                mock_collection = MagicMock()
                mock_collection.count.return_value = 500
                mock_client = MagicMock()
                mock_client.get_collection.return_value = mock_collection
                mock_chromadb.PersistentClient.return_value = mock_client
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    manager = MigrationManager(
                        postgres_conn_params=pg_params,
                        chroma_path=tmpdir,
                    )
                    result = manager.analyze_migration()
        
        assert result['chromadb_count'] == 500
    
    def test_analyze_with_sqlite(self, pg_params, mock_pg_connection):
        """Test analysis with SQLite catalog."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.return_value = (50,)
        
        with patch.object(MigrationManager, '_get_pg_connection', return_value=conn):
            with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
                sqlite_path = f.name
            
            try:
                # Create minimal SQLite database
                import sqlite3
                sqlite_conn = sqlite3.connect(sqlite_path)
                sqlite_conn.execute("CREATE TABLE catalog (id INTEGER PRIMARY KEY)")
                for i in range(25):
                    sqlite_conn.execute("INSERT INTO catalog VALUES (?)", (i,))
                sqlite_conn.commit()
                sqlite_conn.close()
                
                manager = MigrationManager(
                    postgres_conn_params=pg_params,
                    sqlite_path=sqlite_path,
                )
                result = manager.analyze_migration()
                
                assert result['sqlite_count'] == 25
            finally:
                os.unlink(sqlite_path)


# =============================================================================
# Migration State Tests
# =============================================================================

class TestMigrationState:
    """Tests for migration state management."""
    
    def test_start_migration(self, migration_manager, mock_pg_connection):
        """Test starting a new migration."""
        conn, cursor = mock_pg_connection
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            migration_manager.start_migration("test_migration")
        
        # Verify INSERT was executed
        cursor.execute.assert_called()
        conn.commit.assert_called()
    
    def test_update_checkpoint(self, migration_manager, mock_pg_connection):
        """Test updating migration checkpoint."""
        conn, cursor = mock_pg_connection
        
        checkpoint = MigrationCheckpoint(
            phase='vectors',
            last_id=100,
            count=50,
            metadata={'batch': 5},
        )
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            migration_manager.update_checkpoint("test_migration", checkpoint)
        
        cursor.execute.assert_called()
        call_args = cursor.execute.call_args[0]
        assert 'UPDATE migration_state' in call_args[0]
    
    def test_complete_migration(self, migration_manager, mock_pg_connection):
        """Test completing a migration."""
        conn, cursor = mock_pg_connection
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            migration_manager.complete_migration("test_migration")
        
        call_args = cursor.execute.call_args[0]
        assert "status = 'completed'" in call_args[0]
    
    def test_fail_migration(self, migration_manager, mock_pg_connection):
        """Test marking migration as failed."""
        conn, cursor = mock_pg_connection
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            migration_manager.fail_migration("test_migration", "Connection lost")
        
        call_args = cursor.execute.call_args[0]
        assert "status = 'failed'" in call_args[0]
    
    def test_get_migration_status_not_found(self, migration_manager, mock_pg_connection):
        """Test getting status for non-existent migration."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.return_value = None
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            status = migration_manager.get_migration_status("nonexistent")
        
        assert status is None
    
    def test_get_migration_status_completed(self, migration_manager, mock_pg_connection):
        """Test getting status for completed migration."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.return_value = (
            'test_migration',
            datetime(2024, 1, 1),
            datetime(2024, 1, 1, 0, 10),
            'completed',
            None,  # checkpoint
            None,  # error_message
        )
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            status = migration_manager.get_migration_status("test_migration")
        
        assert status.name == "test_migration"
        assert status.status == "completed"


# =============================================================================
# ChromaDB Migration Tests
# =============================================================================

class TestChromaDBMigration:
    """Tests for ChromaDB → PostgreSQL migration."""
    
    def test_migrate_chromadb_not_installed(self, migration_manager, mock_pg_connection):
        """Test migration when chromadb not installed."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.return_value = None  # No existing migration
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            with patch.dict('sys.modules', {'chromadb': None}):
                result = migration_manager.migrate_chromadb()
        
        assert result['status'] == 'error'
        assert 'not installed' in result.get('message', '')
    
    def test_migrate_chromadb_no_path(self, migration_manager, mock_pg_connection):
        """Test migration with no ChromaDB path."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.return_value = None
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            result = migration_manager.migrate_chromadb()
        
        assert result['status'] == 'error'
        assert 'path' in result.get('message', '').lower()
    
    def test_migrate_chromadb_already_completed(self, migration_manager, mock_pg_connection):
        """Test migration that was already completed."""
        conn, cursor = mock_pg_connection
        
        # Return completed status
        with patch.object(migration_manager, 'get_migration_status') as mock_status:
            mock_status.return_value = MigrationStatus(
                name='chromadb_a2rchi',
                started_at=datetime.now(),
                completed_at=datetime.now(),
                status='completed',
                checkpoint=None,
                error_message=None,
            )
            
            result = migration_manager.migrate_chromadb()
        
        assert result['status'] == 'already_completed'
    
    def test_migrate_chromadb_batch_insert(self, pg_params, mock_pg_connection):
        """Test batch insertion of vectors."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.return_value = None  # No existing migration
        cursor.fetchall.return_value = [('doc1', 1), ('doc2', 2)]  # Document IDs
        
        with patch.object(MigrationManager, '_get_pg_connection', return_value=conn):
            with patch('src.utils.migration_manager.chromadb') as mock_chromadb:
                # Mock ChromaDB collection
                mock_collection = MagicMock()
                mock_collection.count.return_value = 2
                mock_collection.get.return_value = {
                    'ids': ['chunk1', 'chunk2'],
                    'embeddings': [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
                    'documents': ['text1', 'text2'],
                    'metadatas': [{'doc_id': 'doc1'}, {'doc_id': 'doc2'}],
                }
                mock_client = MagicMock()
                mock_client.get_collection.return_value = mock_collection
                mock_chromadb.PersistentClient.return_value = mock_client
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    manager = MigrationManager(
                        postgres_conn_params=pg_params,
                        chroma_path=tmpdir,
                    )
                    
                    with patch.object(manager, 'start_migration'):
                        with patch.object(manager, 'complete_migration'):
                            with patch.object(manager, 'update_checkpoint'):
                                with patch('src.utils.migration_manager.execute_values'):
                                    result = manager.migrate_chromadb()
        
        assert result['status'] == 'completed'
        assert result['migrated'] == 2


# =============================================================================
# SQLite Migration Tests
# =============================================================================

class TestSQLiteMigration:
    """Tests for SQLite catalog → PostgreSQL migration."""
    
    def test_migrate_sqlite_no_path(self, migration_manager, mock_pg_connection):
        """Test migration with no SQLite path."""
        conn, cursor = mock_pg_connection
        
        result = migration_manager.migrate_sqlite_catalog()
        
        assert result['status'] == 'skipped'
    
    def test_migrate_sqlite_file_not_found(self, pg_params, mock_pg_connection):
        """Test migration with non-existent file."""
        conn, cursor = mock_pg_connection
        
        with patch.object(MigrationManager, '_get_pg_connection', return_value=conn):
            manager = MigrationManager(
                postgres_conn_params=pg_params,
                sqlite_path="/nonexistent/catalog.sqlite",
            )
            result = manager.migrate_sqlite_catalog()
        
        assert result['status'] == 'skipped'


# =============================================================================
# Conversation Schema Migration Tests
# =============================================================================

class TestConversationSchemaMigration:
    """Tests for conversation schema migration."""
    
    def test_update_conversation_schema(self, migration_manager, mock_pg_connection):
        """Test updating conversation schema."""
        conn, cursor = mock_pg_connection
        cursor.rowcount = 150  # 150 rows updated
        cursor.fetchone.return_value = None  # No existing migration
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            with patch.object(migration_manager, 'start_migration'):
                with patch.object(migration_manager, 'complete_migration'):
                    result = migration_manager.update_conversation_schema()
        
        assert result['status'] == 'completed'
        assert result['updated'] == 150


# =============================================================================
# Configs Table Cleanup Tests
# =============================================================================

class TestConfigsTableCleanup:
    """Tests for configs table analysis and cleanup."""
    
    def test_analyze_configs_table_not_exists(self, migration_manager, mock_pg_connection):
        """Test analysis when configs table doesn't exist."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.return_value = (False,)  # Table doesn't exist
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            result = migration_manager.analyze_configs_table()
        
        assert result['exists'] is False
        assert result['total_rows'] == 0
    
    def test_analyze_configs_table_with_data(self, migration_manager, mock_pg_connection):
        """Test analysis with configs table data."""
        conn, cursor = mock_pg_connection
        
        # Mock sequential fetchone calls
        cursor.fetchone.side_effect = [
            (True,),   # Table exists
            (73000,),  # Total rows
            (500,),    # Unique configs
            (450,),    # Referenced by conversations
            (72550,),  # Orphaned configs
        ]
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            result = migration_manager.analyze_configs_table()
        
        assert result['exists'] is True
        assert result['total_rows'] == 73000
        assert result['unique_configs'] == 500
        assert result['duplication_ratio'] == 146.0
    
    def test_drop_configs_table_not_exists(self, migration_manager, mock_pg_connection):
        """Test dropping non-existent configs table."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.return_value = (False,)  # Table doesn't exist
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            result = migration_manager.drop_configs_table()
        
        assert result['status'] == 'skipped'
    
    def test_drop_configs_table_blocked_by_unmigrated(self, migration_manager, mock_pg_connection):
        """Test drop blocked when conversations not migrated."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.side_effect = [
            (True,),   # Table exists
            (1000,),   # Row count
            (50,),     # Unmigrated conversations
        ]
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            result = migration_manager.drop_configs_table()
        
        assert result['status'] == 'blocked'
        assert 'migrate_conversation_schema' in result.get('message', '')
    
    def test_drop_configs_table_success(self, migration_manager, mock_pg_connection):
        """Test successful configs table drop."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.side_effect = [
            (True,),   # Table exists
            (1000,),   # Row count
            (0,),      # No unmigrated conversations
            (1000,),   # Backup row count
        ]
        cursor.fetchall.return_value = []  # No FK constraints
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            result = migration_manager.drop_configs_table(backup=True)
        
        assert result['status'] == 'completed'
        assert result['table_dropped'] is True
        assert result['rows_backed_up'] == 1000


# =============================================================================
# Resume Functionality Tests
# =============================================================================

class TestMigrationResume:
    """Tests for migration resume functionality."""
    
    def test_chromadb_resume_from_checkpoint(self, pg_params, mock_pg_connection):
        """Test resuming ChromaDB migration from checkpoint."""
        conn, cursor = mock_pg_connection
        cursor.fetchall.return_value = [('doc1', 1)]
        
        with patch.object(MigrationManager, '_get_pg_connection', return_value=conn):
            with patch('src.utils.migration_manager.chromadb') as mock_chromadb:
                mock_collection = MagicMock()
                mock_collection.count.return_value = 200
                mock_collection.get.return_value = {
                    'ids': ['chunk101'],
                    'embeddings': [[0.1, 0.2]],
                    'documents': ['text'],
                    'metadatas': [{'doc_id': 'doc1'}],
                }
                mock_client = MagicMock()
                mock_client.get_collection.return_value = mock_collection
                mock_chromadb.PersistentClient.return_value = mock_client
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    manager = MigrationManager(
                        postgres_conn_params=pg_params,
                        chroma_path=tmpdir,
                    )
                    
                    # Mock existing checkpoint at offset 100
                    with patch.object(manager, 'get_migration_status') as mock_status:
                        mock_status.return_value = MigrationStatus(
                            name='chromadb_a2rchi',
                            started_at=datetime.now(),
                            completed_at=None,
                            status='in_progress',
                            checkpoint=MigrationCheckpoint(
                                phase='vectors',
                                last_id=100,
                                count=100,
                            ),
                            error_message=None,
                        )
                        
                        with patch.object(manager, 'start_migration'):
                            with patch.object(manager, 'complete_migration'):
                                with patch.object(manager, 'update_checkpoint'):
                                    with patch('src.utils.migration_manager.execute_values'):
                                        result = manager.migrate_chromadb(resume=True)
        
        # Should have started from offset 100
        mock_collection.get.assert_called()
        call_kwargs = mock_collection.get.call_args[1]
        assert call_kwargs.get('offset', 0) >= 100


# =============================================================================
# Integration-Style Tests (with sample data)
# =============================================================================

class TestMigrationWithSampleData:
    """Tests with realistic sample data."""
    
    def test_full_migration_dry_run(self, pg_params, mock_pg_connection):
        """Test full migration analysis."""
        conn, cursor = mock_pg_connection
        cursor.fetchone.return_value = (0,)  # conversations
        
        with patch.object(MigrationManager, '_get_pg_connection', return_value=conn):
            manager = MigrationManager(postgres_conn_params=pg_params)
            result = manager.analyze_migration()
        
        assert 'chromadb_count' in result
        assert 'sqlite_count' in result
        assert 'conversations_count' in result
        assert 'estimated_minutes' in result
    
    def test_vector_batch_insert_formats_correctly(self, migration_manager, mock_pg_connection):
        """Test that vector batch insert formats data correctly."""
        conn, cursor = mock_pg_connection
        cursor.fetchall.return_value = [('doc_abc', 1)]
        
        # Sample data matching ChromaDB output
        ids = ['chunk_1', 'chunk_2']
        embeddings = [[0.1] * 384, [0.2] * 384]  # 384-dim vectors
        documents = ['First chunk text', 'Second chunk text']
        metadatas = [
            {'doc_id': 'doc_abc', 'chunk_index': 0, 'source': 'web'},
            {'doc_id': 'doc_abc', 'chunk_index': 1, 'source': 'web'},
        ]
        
        with patch.object(migration_manager, '_get_pg_connection', return_value=conn):
            with patch('src.utils.migration_manager.execute_values') as mock_exec:
                count = migration_manager._insert_vector_batch(
                    conn, ids, embeddings, documents, metadatas
                )
        
        # Verify execute_values was called for documents and chunks
        assert mock_exec.call_count >= 1
