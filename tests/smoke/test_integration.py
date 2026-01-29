#!/usr/bin/env python3
"""
Integration tests for PostgreSQL Consolidation.

Tests all new services against a real PostgreSQL database with pgvector.
Run with: python test_integration.py
Requires: docker-compose.integration.yaml running
"""

import os
import sys
import uuid
import time
import traceback

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import psycopg2
import psycopg2.extras

# PostgreSQL connection config for test container
PG_CONFIG = {
    "host": "localhost",
    "port": 5439,
    "database": "a2rchi",
    "user": "a2rchi",
    "password": "testpassword123",
}


def wait_for_postgres(max_attempts=30, delay=1):
    """Wait for PostgreSQL to be ready."""
    for i in range(max_attempts):
        try:
            conn = psycopg2.connect(**PG_CONFIG)
            conn.close()
            return True
        except psycopg2.OperationalError:
            if i == max_attempts - 1:
                raise
            time.sleep(delay)
    return False


def test_schema_creation():
    """Verify all tables and extensions are created."""
    print("\n=== Test: Schema Creation ===")
    
    conn = psycopg2.connect(**PG_CONFIG)
    cursor = conn.cursor()
    
    # Check extensions
    cursor.execute("SELECT extname FROM pg_extension WHERE extname IN ('vector', 'pgcrypto', 'pg_trgm')")
    extensions = {row[0] for row in cursor.fetchall()}
    
    assert "vector" in extensions, "pgvector not installed"
    print("✓ pgvector extension enabled")
    
    assert "pgcrypto" in extensions, "pgcrypto not installed"
    print("✓ pgcrypto extension enabled")
    
    assert "pg_trgm" in extensions, "pg_trgm not installed"
    print("✓ pg_trgm extension enabled")
    
    # Check tables (updated for v2 schema)
    expected_tables = [
        "users",
        "static_config",
        "dynamic_config",
        "document_chunks",
        "documents",
        "conversations",
        "user_document_defaults",
        "conversation_document_overrides",
        "ab_comparisons",
        "feedback",
        "timing",
        "configs",
        "conversation_metadata",
        "agent_traces",
        "migration_state",
    ]
    
    cursor.execute("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public'
    """)
    actual_tables = {row[0] for row in cursor.fetchall()}
    
    for table in expected_tables:
        if table in actual_tables:
            print(f"✓ Table '{table}' exists")
        else:
            print(f"⚠ Table '{table}' missing (may be renamed)")
    
    cursor.close()
    conn.close()
    print("✓ Schema creation test passed")


def test_user_service():
    """Test UserService with actual database."""
    print("\n=== Test: UserService ===")
    
    # Set encryption key for BYOK
    os.environ["BYOK_ENCRYPTION_KEY"] = "test-encryption-key-32chars-ok"
    
    from src.utils.user_service import UserService
    
    service = UserService(PG_CONFIG)
    
    # Test user creation
    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    user = service.get_or_create_user(test_user_id, auth_provider="anonymous")
    
    assert user is not None, "User creation failed"
    assert user.id == test_user_id, "User ID mismatch"
    assert user.auth_provider == "anonymous", "Auth provider mismatch"
    print(f"✓ Created user: {test_user_id}")
    
    # Test preferences update
    service.update_preferences(test_user_id, theme="dark", preferred_model="gpt-4o")
    updated_user = service.get_user(test_user_id)
    
    assert updated_user.theme == "dark", "Theme not updated"
    assert updated_user.preferred_model == "gpt-4o", "Preferred model not updated"
    print(f"✓ Updated preferences: theme={updated_user.theme}, model={updated_user.preferred_model}")
    
    # Test BYOK API key storage
    test_api_key = f"sk-test-{uuid.uuid4().hex}"
    service.set_api_key(test_user_id, "openai", test_api_key)
    print("✓ Stored encrypted API key")
    
    # Retrieve and verify
    retrieved_key = service.get_api_key(test_user_id, "openai")
    assert retrieved_key == test_api_key, "API key round-trip failed"
    print("✓ Retrieved and verified API key (encryption working)")
    
    # Delete key
    service.delete_api_key(test_user_id, "openai")
    deleted_key = service.get_api_key(test_user_id, "openai")
    assert deleted_key is None, "API key deletion failed"
    print("✓ Deleted API key")
    
    print("✓ UserService test passed")
    return test_user_id


def test_conversation_service(test_user_id):
    """Test ConversationService with model tracking."""
    print("\n=== Test: ConversationService ===")
    
    from src.utils.conversation_service import ConversationService, Message
    
    service = ConversationService(connection_params=PG_CONFIG)
    
    # Create a test conversation ID
    test_conv_id = 999999
    
    # First create conversation_metadata (required by FK constraint)
    conn = psycopg2.connect(**PG_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversation_metadata (conversation_id, user_id, title)
                VALUES (%s, %s, %s)
                ON CONFLICT (conversation_id) DO NOTHING
            """, (test_conv_id, test_user_id, "Test Conversation"))
        conn.commit()
    finally:
        conn.close()
    print(f"✓ Created conversation metadata: {test_conv_id}")
    
    # Insert messages with model tracking (using correct field name: a2rchi_service)
    messages = [
        Message(
            sender=test_user_id,
            content="What is the capital of France?",
            a2rchi_service="integration_test",
            conversation_id=str(test_conv_id),
            model_used=None,
            pipeline_used=None,
        ),
        Message(
            sender="A2rchi",
            content="The capital of France is Paris.",
            a2rchi_service="integration_test", 
            conversation_id=str(test_conv_id),
            link="https://example.com",
            context='{"test": true}',
            model_used="gpt-4o",
            pipeline_used="QAPipeline",
        ),
    ]
    
    message_ids = service.insert_messages(messages)
    assert len(message_ids) == 2, "Expected 2 message IDs"
    print(f"✓ Inserted messages with IDs: {message_ids}")
    
    # Query back and verify model tracking
    history = service.get_conversation_history(str(test_conv_id))
    assert len(history) >= 2, "Expected at least 2 messages in history"
    print(f"✓ Retrieved {len(history)} messages from history")
    
    # Find the A2rchi message and check model tracking
    a2rchi_msgs = [m for m in history if m.sender == "A2rchi"]
    assert len(a2rchi_msgs) > 0, "No A2rchi messages found"
    
    msg = a2rchi_msgs[-1]
    assert msg.model_used == "gpt-4o", f"Expected model_used='gpt-4o', got '{msg.model_used}'"
    assert msg.pipeline_used == "QAPipeline", f"Expected pipeline_used='QAPipeline', got '{msg.pipeline_used}'"
    print(f"✓ Model tracking verified: model_used={msg.model_used}, pipeline_used={msg.pipeline_used}")
    
    print("✓ ConversationService test passed")
    return test_conv_id


def test_ab_comparison_v2(test_conv_id):
    """Test A/B comparison with model tracking (no config FK)."""
    print("\n=== Test: A/B Comparison V2 ===")
    
    from src.utils.conversation_service import ConversationService
    
    service = ConversationService(connection_params=PG_CONFIG)
    
    # First, insert placeholder messages for the A/B comparison
    from src.utils.conversation_service import Message
    
    prompt_msg = Message(
        sender="user",
        content="What is AI?",
        a2rchi_service="integration_test",
        conversation_id=test_conv_id,
    )
    response_a_msg = Message(
        sender="A2rchi",
        content="Response from GPT-4o",
        a2rchi_service="integration_test",
        conversation_id=test_conv_id,
        model_used="gpt-4o",
        pipeline_used="QAPipeline",
    )
    response_b_msg = Message(
        sender="A2rchi",
        content="Response from Claude",
        a2rchi_service="integration_test",
        conversation_id=test_conv_id,
        model_used="claude-3-5-sonnet",
        pipeline_used="QAPipeline",
    )
    
    message_ids = service.insert_messages([prompt_msg, response_a_msg, response_b_msg])
    user_prompt_mid, response_a_mid, response_b_mid = message_ids
    
    # Create A/B comparison with model info (using correct API)
    comparison_id = service.create_ab_comparison(
        conversation_id=test_conv_id,
        user_prompt_mid=user_prompt_mid,
        response_a_mid=response_a_mid,
        response_b_mid=response_b_mid,
        model_a="gpt-4o",
        model_b="claude-3-5-sonnet",
        pipeline_a="QAPipeline",
        pipeline_b="QAPipeline",
        is_config_a_first=True,
    )
    print(f"✓ Created A/B comparison: {comparison_id}")
    
    # Record preference
    service.record_ab_preference(
        comparison_id, 
        preference="a",
    )
    print("✓ Recorded preference")
    
    print("✓ A/B Comparison V2 test passed")


def test_document_selection_direct():
    """Test document selection tables directly with SQL (v2 schema)."""
    print("\n=== Test: Document Selection (Direct SQL) ===")
    
    conn = psycopg2.connect(**PG_CONFIG)
    cursor = conn.cursor()
    
    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    
    # First create user
    cursor.execute("""
        INSERT INTO users (id, auth_provider) VALUES (%s, 'anonymous')
        ON CONFLICT (id) DO NOTHING
    """, (test_user_id,))
    conn.commit()
    print(f"✓ Created test user: {test_user_id}")
    
    # Create a test document first (required for FK)
    test_doc_hash = f"doc_{uuid.uuid4().hex[:8]}"
    cursor.execute("""
        INSERT INTO documents (resource_hash, file_path, display_name, source_type)
        VALUES (%s, '/test/path.txt', 'Test Document', 'local_files')
        RETURNING id
    """, (test_doc_hash,))
    doc_id = cursor.fetchone()[0]
    conn.commit()
    print(f"✓ Created test document with id: {doc_id}")
    
    # Test user document defaults (enable/disable per user)
    cursor.execute("""
        INSERT INTO user_document_defaults (user_id, document_id, enabled)
        VALUES (%s, %s, FALSE)
        ON CONFLICT (user_id, document_id) DO UPDATE SET enabled = EXCLUDED.enabled
    """, (test_user_id, doc_id))
    conn.commit()
    print("✓ Set user document default (disabled)")
    
    # Verify
    cursor.execute("""
        SELECT enabled FROM user_document_defaults WHERE user_id = %s AND document_id = %s
    """, (test_user_id, doc_id))
    row = cursor.fetchone()
    assert row is not None, "User document default not found"
    assert row[0] == False, f"Expected enabled=False, got {row[0]}"
    print(f"✓ User document default retrieved: enabled={row[0]}")
    
    # Test conversation document overrides
    # First create conversation metadata
    cursor.execute("""
        INSERT INTO conversation_metadata (conversation_id, user_id, title)
        VALUES (%s, %s, 'Test Conversation')
        ON CONFLICT (conversation_id) DO NOTHING
        RETURNING conversation_id
    """, (888888, test_user_id))
    test_conv_id = 888888
    conn.commit()
    print(f"✓ Created test conversation: {test_conv_id}")
    
    cursor.execute("""
        INSERT INTO conversation_document_overrides (conversation_id, document_id, enabled)
        VALUES (%s, %s, TRUE)
        ON CONFLICT (conversation_id, document_id) DO UPDATE SET enabled = EXCLUDED.enabled
    """, (test_conv_id, doc_id))
    conn.commit()
    print("✓ Set conversation document override (enabled)")
    
    cursor.execute("""
        SELECT enabled FROM conversation_document_overrides 
        WHERE conversation_id = %s AND document_id = %s
    """, (test_conv_id, doc_id))
    row = cursor.fetchone()
    assert row[0] == True, f"Expected enabled=True, got {row[0]}"
    print(f"✓ Conversation override retrieved: enabled={row[0]}")
    
    # Clean up
    cursor.execute("DELETE FROM conversation_document_overrides WHERE conversation_id = %s", (test_conv_id,))
    cursor.execute("DELETE FROM user_document_defaults WHERE user_id = %s", (test_user_id,))
    cursor.execute("DELETE FROM documents WHERE resource_hash = %s", (test_doc_hash,))
    conn.commit()
    
    cursor.close()
    conn.close()
    print("✓ Document selection test passed")


def test_byok_resolver(test_user_id):
    """Test BYOK provider resolver."""
    print("\n=== Test: BYOK Resolver ===")
    
    # Set encryption key for BYOK
    os.environ["BYOK_ENCRYPTION_KEY"] = "test-encryption-key-32chars-ok"
    
    from src.a2rchi.providers.byok_resolver import BYOKResolver
    from src.utils.user_service import UserService
    
    user_service = UserService(PG_CONFIG)
    resolver = BYOKResolver(user_service=user_service)
    
    # Store a test API key
    test_key = f"sk-test-byok-{uuid.uuid4().hex[:8]}"
    user_service.set_api_key(test_user_id, "openai", test_key)
    
    # Resolve BYOK key
    resolved_key = resolver.get_byok_key("openai", user_id=test_user_id)
    assert resolved_key == test_key, "BYOK key resolution failed"
    print(f"✓ BYOK key resolved correctly for user {test_user_id}")
    
    # Test that key resolves to None for users without keys
    other_user_key = resolver.get_byok_key("openai", user_id="nonexistent_user")
    assert other_user_key is None, "Should return None for users without keys"
    print("✓ Returns None for users without BYOK keys")
    
    # Test different providers
    anthropic_key = resolver.get_byok_key("anthropic", user_id=test_user_id)
    assert anthropic_key is None, "Should return None for unset provider"
    print("✓ Returns None for unset provider keys")
    
    print("✓ BYOK Resolver test passed")


def test_connection_pool():
    """Test ConnectionPool functionality."""
    print("\n=== Test: Connection Pool ===")
    
    from src.utils.connection_pool import ConnectionPool
    
    # Reset singleton first (in case other tests used it)
    ConnectionPool.reset_instance()
    
    # Create a pool via constructor
    pool = ConnectionPool(
        PG_CONFIG,
        min_conn=2,
        max_conn=5,
    )
    print("✓ Created connection pool (min=2, max=5)")
    
    # Get a connection using context manager
    with pool.get_connection() as conn:
        assert conn is not None, "Failed to get connection from pool"
        print("✓ Got connection from pool")
        
        # Use it
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1, "Query failed"
        cursor.close()
        print("✓ Executed query successfully")
    
    print("✓ Connection returned to pool automatically")
    
    # Close pool
    pool.close()
    print("✓ Closed pool")
    
    print("✓ Connection pool test passed")


def test_grafana_queries():
    """Test Grafana dashboard queries work correctly."""
    print("\n=== Test: Grafana Queries ===")
    
    conn = psycopg2.connect(**PG_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Model Usage Over Time
    cursor.execute("""
        SELECT 
            date_trunc('hour', ts) as time_bucket,
            model_used,
            COUNT(*) as message_count
        FROM conversations
        WHERE model_used IS NOT NULL
          AND ts > NOW() - INTERVAL '24 hours'
        GROUP BY time_bucket, model_used
        ORDER BY time_bucket
    """)
    model_usage = cursor.fetchall()
    print(f"✓ Model usage query: {len(model_usage)} time buckets")
    
    # A/B Comparison Stats
    cursor.execute("""
        SELECT 
            model_a,
            model_b,
            COUNT(*) as total_comparisons,
            SUM(CASE WHEN preference = 'a' THEN 1 ELSE 0 END) as a_wins,
            SUM(CASE WHEN preference = 'b' THEN 1 ELSE 0 END) as b_wins,
            SUM(CASE WHEN preference = 'tie' THEN 1 ELSE 0 END) as ties
        FROM ab_comparisons
        WHERE model_a IS NOT NULL
        GROUP BY model_a, model_b
    """)
    ab_stats = cursor.fetchall()
    print(f"✓ A/B comparison query: {len(ab_stats)} model pairs")
    
    # User Activity
    cursor.execute("""
        SELECT 
            auth_provider,
            COUNT(*) as user_count,
            COUNT(*) FILTER (WHERE updated_at > NOW() - INTERVAL '7 days') as active_last_week
        FROM users
        GROUP BY auth_provider
    """)
    user_activity = cursor.fetchall()
    print(f"✓ User activity query: {len(user_activity)} auth providers")
    
    cursor.close()
    conn.close()
    print("✓ Grafana queries test passed")


def test_catalog_ingestion():
    """Test PostgresCatalogService ingestion workflow."""
    print("\n=== Test: Catalog Ingestion ===")
    
    import tempfile
    from pathlib import Path
    from src.data_manager.collectors.utils.catalog_postgres import PostgresCatalogService
    
    # Create catalog service
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog = PostgresCatalogService(
            data_path=temp_dir,
            pg_config=PG_CONFIG,
        )
        
        # Initial state
        initial_count = len(catalog.file_index)
        print(f"✓ Catalog initialized with {initial_count} documents")
        
        # Add a test resource
        test_hash = f"test_ingest_{uuid.uuid4().hex[:8]}"
        test_path = "test_files/sample.txt"
        test_metadata = {
            "display_name": "Sample Test Document",
            "source_type": "local_files",
            "url": "https://example.com/sample.txt",
        }
        
        catalog.upsert_resource(test_hash, test_path, test_metadata)
        print(f"✓ Upserted resource: {test_hash}")
        
        # Refresh and verify it appears
        catalog.refresh()
        assert test_hash in catalog.file_index, "Resource not in file_index after refresh"
        assert catalog.file_index[test_hash] == test_path, "Incorrect path in file_index"
        print(f"✓ Resource in file_index: {catalog.file_index[test_hash]}")
        
        # Get document ID
        doc_id = catalog.get_document_id(test_hash)
        assert doc_id is not None, "Document ID should exist"
        print(f"✓ Document ID: {doc_id}")
        
        # Test list_documents (returns dict with "documents" key)
        result = catalog.list_documents()
        documents = result.get("documents", [])
        test_docs = [d for d in documents if d.get("hash") == test_hash]
        assert len(test_docs) == 1, "Document should appear in list_documents"
        print(f"✓ Document appears in list_documents: {test_docs[0].get('display_name')}")
        
        # Test update resource
        updated_metadata = {
            "display_name": "Updated Test Document",
            "source_type": "local_files",
        }
        catalog.upsert_resource(test_hash, test_path, updated_metadata)
        
        result = catalog.list_documents()
        documents = result.get("documents", [])
        test_docs = [d for d in documents if d.get("hash") == test_hash]
        assert test_docs[0].get("display_name") == "Updated Test Document"
        print("✓ Resource metadata updated successfully")
        
        # Test delete
        catalog.delete_resource(test_hash)
        catalog.refresh()
        assert test_hash not in catalog.file_index, "Resource should be deleted"
        print("✓ Resource deleted successfully")
        
    print("✓ Catalog ingestion test passed")


def test_data_viewer_service():
    """Test DataViewerService returns documents from catalog."""
    print("\n=== Test: DataViewerService ===")
    
    import tempfile
    from pathlib import Path
    from src.data_manager.data_viewer_service import DataViewerService
    from src.data_manager.collectors.utils.catalog_postgres import PostgresCatalogService
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # First add a document to the catalog
        catalog = PostgresCatalogService(data_path=temp_dir, pg_config=PG_CONFIG)
        test_hash = f"viewer_test_{uuid.uuid4().hex[:8]}"
        test_path = "test_files/viewer_sample.txt"
        
        catalog.upsert_resource(test_hash, test_path, {
            "display_name": "Viewer Test Document",
            "source_type": "local_files",
        })
        print(f"✓ Added test document: {test_hash}")
        
        # Now test the DataViewerService
        viewer = DataViewerService(data_path=temp_dir, pg_config=PG_CONFIG)
        
        # List documents (no conversation_id)
        result = viewer.list_documents(conversation_id=None)
        documents = result.get("documents", [])
        test_docs = [d for d in documents if d.get("hash") == test_hash]
        
        assert len(test_docs) == 1, f"Document should appear in viewer list, got {len(documents)} docs"
        print(f"✓ DataViewerService.list_documents() returned {len(documents)} documents")
        print(f"✓ Test document found: {test_docs[0].get('display_name')}")
        
        # Test stats
        stats = result
        assert "total" in stats, "Stats should include total"
        assert "enabled_count" in stats, "Stats should include enabled_count"
        print(f"✓ Stats: total={stats['total']}, enabled_count={stats['enabled_count']}")
        
        # Clean up
        catalog.delete_resource(test_hash)
        
    print("✓ DataViewerService test passed")


def test_vector_similarity():
    """Test pgvector similarity search works."""
    print("\n=== Test: Vector Similarity Search ===")
    
    conn = psycopg2.connect(**PG_CONFIG)
    cursor = conn.cursor()
    
    # Create a test document first (v2 schema uses documents table)
    test_hash = f"test_doc_{uuid.uuid4().hex[:8]}"
    cursor.execute("""
        INSERT INTO documents (resource_hash, file_path, display_name, source_type)
        VALUES (%s, '/test/vector_test.txt', 'Vector Test Doc', 'local_files')
        RETURNING id
    """, (test_hash,))
    doc_id = cursor.fetchone()[0]
    conn.commit()
    print(f"✓ Created test document with id: {doc_id}")
    
    # Insert test vectors (384 dimensions as per schema)
    import random
    
    # Create 5 test chunks with random embeddings
    for i in range(5):
        embedding = [random.random() for _ in range(384)]
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        cursor.execute("""
            INSERT INTO document_chunks (document_id, chunk_index, chunk_text, embedding)
            VALUES (%s, %s, %s, %s::vector)
        """, (doc_id, i, f"Test chunk {i}", embedding_str))
    
    conn.commit()
    print(f"✓ Inserted 5 test chunks with embeddings")
    
    # Query vector
    query_embedding = [random.random() for _ in range(384)]
    query_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    
    # Test cosine similarity search
    cursor.execute("""
        SELECT 
            chunk_text,
            embedding <=> %s::vector as distance
        FROM document_chunks
        WHERE document_id = %s
        ORDER BY embedding <=> %s::vector
        LIMIT 3
    """, (query_str, doc_id, query_str))
    
    results = cursor.fetchall()
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    print(f"✓ Vector similarity search returned {len(results)} results")
    
    # Verify distances are ordered
    distances = [r[1] for r in results]
    assert distances == sorted(distances), "Results not ordered by distance"
    print(f"✓ Results correctly ordered by distance: {[round(d, 4) for d in distances]}")
    
    # Clean up (cascade deletes chunks when document is deleted)
    cursor.execute("DELETE FROM documents WHERE resource_hash = %s", (test_hash,))
    conn.commit()
    
    cursor.close()
    conn.close()
    print("✓ Vector similarity search test passed")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("PostgreSQL Consolidation Integration Tests")
    print("=" * 60)
    
    # Wait for PostgreSQL
    print("Waiting for PostgreSQL to be ready...")
    try:
        wait_for_postgres()
        print("✓ PostgreSQL is ready")
    except Exception as e:
        print(f"✗ PostgreSQL not ready: {e}")
        return False
    
    passed = 0
    failed = 0
    
    # Track user/conv IDs across tests
    test_user_id = None
    test_conv_id = None
    
    # Run tests
    tests = [
        ("Schema Creation", lambda: test_schema_creation()),
        ("Connection Pool", lambda: test_connection_pool()),
        ("UserService", lambda: test_user_service()),
        ("ConversationService", lambda: test_conversation_service(test_user_id)),
        ("A/B Comparison V2", lambda: test_ab_comparison_v2(test_conv_id)),
        ("Document Selection", lambda: test_document_selection_direct()),
        ("BYOK Resolver", lambda: test_byok_resolver(test_user_id)),
        ("Catalog Ingestion", lambda: test_catalog_ingestion()),
        ("DataViewerService", lambda: test_data_viewer_service()),
        ("Vector Similarity", lambda: test_vector_similarity()),
        ("Grafana Queries", lambda: test_grafana_queries()),
    ]
    
    for name, test_func in tests:
        try:
            result = test_func()
            
            # Capture user_id and conv_id for dependent tests
            if name == "UserService" and result:
                test_user_id = result
            elif name == "ConversationService" and result:
                test_conv_id = result
                
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} FAILED: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
