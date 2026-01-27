"""
Migration tooling for PostgreSQL consolidation.

Migrates data from:
- ChromaDB → PostgreSQL pgvector
- SQLite catalog → PostgreSQL documents table
- Old conversation schema → New schema with model_used/pipeline_used
"""
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)


@dataclass
class MigrationCheckpoint:
    """Checkpoint for resumable migration."""
    phase: str
    last_id: int
    count: int
    metadata: Optional[Dict[str, Any]] = None


@dataclass 
class MigrationStatus:
    """Status of a migration."""
    name: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: str  # 'in_progress', 'completed', 'failed'
    checkpoint: Optional[MigrationCheckpoint]
    error_message: Optional[str]


class MigrationManager:
    """
    Manages data migration for PostgreSQL consolidation.
    
    Supports:
    - ChromaDB → pgvector migration
    - SQLite catalog → documents table migration
    - Conversation schema migration (conf_id → model_used/pipeline_used)
    - Resumable migrations with checkpointing
    """
    
    # Batch sizes for migration
    BATCH_SIZE_VECTORS = 100
    BATCH_SIZE_DOCUMENTS = 500
    BATCH_SIZE_CONVERSATIONS = 1000
    
    def __init__(
        self,
        postgres_conn_params: Dict[str, Any] = None,
        chroma_path: Optional[str] = None,
        sqlite_path: Optional[str] = None,
        # Alternative parameter names for CLI compatibility
        pg_config: Dict[str, Any] = None,
        chromadb_path: Optional[str] = None,
    ):
        """
        Initialize MigrationManager.
        
        Args:
            postgres_conn_params: PostgreSQL connection parameters
            chroma_path: Path to ChromaDB persistence directory
            sqlite_path: Path to SQLite catalog database
            pg_config: Alias for postgres_conn_params
            chromadb_path: Alias for chroma_path
        """
        self._pg_params = postgres_conn_params or pg_config
        self._chroma_path = chroma_path or chromadb_path
        self._sqlite_path = sqlite_path
    
    def _get_pg_connection(self):
        """Get PostgreSQL connection."""
        return psycopg2.connect(**self._pg_params)
    
    # =========================================================================
    # Migration State Management
    # =========================================================================
    
    def get_migration_status(self, migration_name: str) -> Optional[MigrationStatus]:
        """Get status of a migration."""
        conn = self._get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT migration_name, started_at, completed_at, status, 
                           last_checkpoint, error_message
                    FROM migration_state
                    WHERE migration_name = %s
                """, (migration_name,))
                row = cur.fetchone()
                
                if not row:
                    return None
                
                checkpoint = None
                if row[4]:
                    cp = row[4]
                    checkpoint = MigrationCheckpoint(
                        phase=cp.get('phase', ''),
                        last_id=cp.get('last_id', 0),
                        count=cp.get('count', 0),
                        metadata=cp.get('metadata'),
                    )
                
                return MigrationStatus(
                    name=row[0],
                    started_at=row[1],
                    completed_at=row[2],
                    status=row[3],
                    checkpoint=checkpoint,
                    error_message=row[5],
                )
        finally:
            conn.close()
    
    def start_migration(self, migration_name: str) -> None:
        """Start a new migration or resume existing."""
        conn = self._get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO migration_state (migration_name, status)
                    VALUES (%s, 'in_progress')
                    ON CONFLICT (migration_name) 
                    DO UPDATE SET 
                        started_at = CASE WHEN migration_state.status = 'failed' 
                                          THEN NOW() 
                                          ELSE migration_state.started_at END,
                        status = 'in_progress',
                        error_message = NULL
                    WHERE migration_state.status != 'completed'
                """, (migration_name,))
                conn.commit()
        finally:
            conn.close()
    
    def update_checkpoint(
        self,
        migration_name: str,
        checkpoint: MigrationCheckpoint,
    ) -> None:
        """Update migration checkpoint for resumability."""
        conn = self._get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE migration_state
                    SET last_checkpoint = %s
                    WHERE migration_name = %s
                """, (
                    json.dumps({
                        'phase': checkpoint.phase,
                        'last_id': checkpoint.last_id,
                        'count': checkpoint.count,
                        'metadata': checkpoint.metadata,
                    }),
                    migration_name,
                ))
                conn.commit()
        finally:
            conn.close()
    
    def complete_migration(self, migration_name: str) -> None:
        """Mark migration as completed."""
        conn = self._get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE migration_state
                    SET status = 'completed', completed_at = NOW()
                    WHERE migration_name = %s
                """, (migration_name,))
                conn.commit()
        finally:
            conn.close()
    
    def fail_migration(self, migration_name: str, error: str) -> None:
        """Mark migration as failed."""
        conn = self._get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE migration_state
                    SET status = 'failed', error_message = %s
                    WHERE migration_name = %s
                """, (error, migration_name))
                conn.commit()
        finally:
            conn.close()
    
    def analyze_migration(self) -> Dict[str, Any]:
        """
        Analyze what would be migrated (dry run).
        
        Returns:
            Dictionary with counts and estimates
        """
        result = {
            'chromadb_count': 0,
            'sqlite_count': 0,
            'conversations_count': 0,
            'estimated_minutes': 0,
        }
        
        # Count ChromaDB vectors
        if self._chroma_path and os.path.exists(self._chroma_path):
            try:
                import chromadb
                client = chromadb.PersistentClient(path=self._chroma_path)
                try:
                    collection = client.get_collection("a2rchi")
                    result['chromadb_count'] = collection.count()
                except Exception:
                    pass
            except ImportError:
                pass
        
        # Count SQLite catalog records
        if self._sqlite_path and os.path.exists(self._sqlite_path):
            try:
                import sqlite3
                conn = sqlite3.connect(self._sqlite_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM catalog")
                result['sqlite_count'] = cursor.fetchone()[0]
                conn.close()
            except Exception:
                pass
        
        # Count conversations needing model_used update
        try:
            pg_conn = self._get_pg_connection()
            with pg_conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM conversations 
                    WHERE model_used IS NULL AND sender = 'A2rchi'
                """)
                result['conversations_count'] = cur.fetchone()[0]
            pg_conn.close()
        except Exception:
            pass
        
        # Estimate time (rough: ~1000 records per minute)
        total_records = (
            result['chromadb_count'] + 
            result['sqlite_count'] + 
            result['conversations_count']
        )
        result['estimated_minutes'] = max(1, total_records // 1000)
        
        return result
    
    def migrate_sqlite_catalog(self, batch_size: int = 500) -> Dict[str, Any]:
        """
        Migrate SQLite catalog to PostgreSQL resources table.
        
        Args:
            batch_size: Records per batch
            
        Returns:
            Migration statistics
        """
        if not self._sqlite_path or not os.path.exists(self._sqlite_path):
            return {"status": "skipped", "message": "SQLite catalog not found", "migrated": 0}
        
        try:
            import sqlite3
        except ImportError:
            return {"status": "error", "message": "sqlite3 not available"}
        
        migration_name = "sqlite_catalog"
        self.start_migration(migration_name)
        
        errors = []
        migrated = 0
        
        try:
            sqlite_conn = sqlite3.connect(self._sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cursor = sqlite_conn.cursor()
            
            pg_conn = self._get_pg_connection()
            
            # Get total count
            sqlite_cursor.execute("SELECT COUNT(*) FROM catalog")
            total_count = sqlite_cursor.fetchone()[0]
            logger.info(f"Found {total_count} records in SQLite catalog")
            
            # Migrate in batches
            offset = 0
            while offset < total_count:
                sqlite_cursor.execute("""
                    SELECT resource_hash, filename, url, local_path, 
                           doc_type, num_chunks, created_at
                    FROM catalog
                    LIMIT ? OFFSET ?
                """, (batch_size, offset))
                
                rows = sqlite_cursor.fetchall()
                if not rows:
                    break
                
                # Prepare data for PostgreSQL
                values = []
                for row in rows:
                    values.append((
                        row['resource_hash'],
                        row['filename'],
                        row['url'],
                        row['local_path'],
                        row['doc_type'],
                        row['num_chunks'],
                        row['created_at'],
                    ))
                
                # Insert into PostgreSQL
                with pg_conn.cursor() as cur:
                    execute_values(
                        cur,
                        """
                        INSERT INTO resources 
                            (resource_hash, filename, url, local_path, doc_type, num_chunks, created_at)
                        VALUES %s
                        ON CONFLICT (resource_hash) DO NOTHING
                        """,
                        values,
                    )
                pg_conn.commit()
                
                migrated += len(rows)
                offset += batch_size
                
                # Update checkpoint
                self.update_checkpoint(
                    migration_name,
                    MigrationCheckpoint(phase='catalog', last_id=offset, count=migrated)
                )
                
                logger.info(f"Migrated {migrated}/{total_count} catalog records")
            
            sqlite_conn.close()
            pg_conn.close()
            
            self.complete_migration(migration_name)
            return {"status": "completed", "migrated": migrated, "errors": errors}
            
        except Exception as e:
            self.fail_migration(migration_name, str(e))
            return {"status": "error", "message": str(e), "migrated": migrated, "errors": errors}
    
    def update_conversation_schema(self) -> Dict[str, Any]:
        """
        Update conversations to populate model_used from config.
        
        For existing conversations that have conf_id but no model_used,
        attempts to extract model information from the linked config.
        
        Returns:
            Migration statistics
        """
        migration_name = "conversation_schema"
        self.start_migration(migration_name)
        
        updated = 0
        
        try:
            pg_conn = self._get_pg_connection()
            
            with pg_conn.cursor() as cur:
                # Update model_used from configs table where available
                cur.execute("""
                    UPDATE conversations c
                    SET model_used = 'legacy-config-' || COALESCE(c.conf_id::text, 'unknown')
                    WHERE c.model_used IS NULL
                      AND c.sender = 'A2rchi'
                """)
                updated = cur.rowcount
            
            pg_conn.commit()
            pg_conn.close()
            
            self.complete_migration(migration_name)
            return {"status": "completed", "updated": updated}
            
        except Exception as e:
            self.fail_migration(migration_name, str(e))
            return {"status": "error", "message": str(e), "updated": updated}

    # =========================================================================
    # ChromaDB → pgvector Migration
    # =========================================================================
    
    def migrate_chromadb(
        self,
        collection_name: str = "a2rchi",
        resume: bool = True,
    ) -> Dict[str, Any]:
        """
        Migrate ChromaDB vectors to PostgreSQL pgvector.
        
        Args:
            collection_name: ChromaDB collection name
            resume: Whether to resume from checkpoint
            
        Returns:
            Migration statistics
        """
        migration_name = f"chromadb_{collection_name}"
        
        # Check if already completed
        status = self.get_migration_status(migration_name)
        if status and status.status == 'completed':
            logger.info(f"Migration {migration_name} already completed")
            return {"status": "already_completed", "count": 0}
        
        try:
            import chromadb
        except ImportError:
            logger.error("chromadb package not installed - cannot migrate")
            return {"status": "error", "message": "chromadb not installed"}
        
        if not self._chroma_path:
            return {"status": "error", "message": "ChromaDB path not provided"}
        
        self.start_migration(migration_name)
        
        try:
            # Connect to ChromaDB
            client = chromadb.PersistentClient(path=self._chroma_path)
            collection = client.get_collection(collection_name)
            
            # Get total count
            total_count = collection.count()
            logger.info(f"Found {total_count} vectors in ChromaDB collection '{collection_name}'")
            
            # Resume from checkpoint if available
            start_offset = 0
            migrated_count = 0
            if resume and status and status.checkpoint:
                start_offset = status.checkpoint.last_id
                migrated_count = status.checkpoint.count
                logger.info(f"Resuming from offset {start_offset}, {migrated_count} already migrated")
            
            # Migrate in batches
            pg_conn = self._get_pg_connection()
            try:
                offset = start_offset
                while offset < total_count:
                    # Get batch from ChromaDB
                    result = collection.get(
                        include=["embeddings", "metadatas", "documents"],
                        limit=self.BATCH_SIZE_VECTORS,
                        offset=offset,
                    )
                    
                    if not result['ids']:
                        break
                    
                    # Insert into PostgreSQL
                    batch_count = self._insert_vector_batch(
                        pg_conn,
                        result['ids'],
                        result['embeddings'],
                        result['documents'],
                        result['metadatas'],
                    )
                    
                    migrated_count += batch_count
                    offset += len(result['ids'])
                    
                    # Update checkpoint
                    self.update_checkpoint(migration_name, MigrationCheckpoint(
                        phase='vectors',
                        last_id=offset,
                        count=migrated_count,
                    ))
                    
                    logger.info(f"Migrated {migrated_count}/{total_count} vectors")
                
                self.complete_migration(migration_name)
                return {
                    "status": "completed",
                    "total": total_count,
                    "migrated": migrated_count,
                }
            finally:
                pg_conn.close()
                
        except Exception as e:
            self.fail_migration(migration_name, str(e))
            logger.error(f"Migration failed: {e}")
            raise
    
    def _insert_vector_batch(
        self,
        conn,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict],
    ) -> int:
        """Insert batch of vectors into pgvector."""
        # Map ChromaDB metadata to document + chunk structure
        # ChromaDB stores: {doc_id, chunk_index, source, ...}
        
        values = []
        for i, (id_, embedding, doc, meta) in enumerate(zip(ids, embeddings, documents, metadatas)):
            # Extract document info from metadata
            doc_id = meta.get('doc_id') or meta.get('document_id')
            chunk_idx = meta.get('chunk_index', 0)
            
            if doc_id is None:
                # Generate doc_id from content hash
                doc_id = hashlib.sha256(doc.encode()).hexdigest()[:16]
            
            values.append((
                doc_id,
                chunk_idx,
                doc,  # chunk_text
                embedding,  # embedding vector
                json.dumps(meta),  # metadata as JSONB
            ))
        
        with conn.cursor() as cur:
            # First ensure documents exist
            doc_values = []
            seen_docs = set()
            for v in values:
                doc_id = v[0]
                if doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    doc_values.append((
                        doc_id,  # resource_hash
                        f"migrated_{doc_id}",  # file_path placeholder
                        f"Document {doc_id}",  # display_name
                        'unknown',  # source_type
                    ))
            
            # Insert documents (ignore conflicts)
            execute_values(
                cur,
                """
                INSERT INTO documents (resource_hash, file_path, display_name, source_type)
                VALUES %s
                ON CONFLICT (resource_hash) DO NOTHING
                """,
                doc_values,
            )
            
            # Get document IDs mapping
            cur.execute("""
                SELECT resource_hash, id FROM documents 
                WHERE resource_hash = ANY(%s)
            """, ([v[0] for v in values],))
            doc_id_map = {row[0]: row[1] for row in cur.fetchall()}
            
            # Insert chunks
            chunk_values = [
                (
                    doc_id_map[v[0]],  # document_id
                    v[1],  # chunk_index
                    v[2],  # chunk_text
                    v[3],  # embedding
                    v[4],  # metadata
                )
                for v in values
                if v[0] in doc_id_map
            ]
            
            execute_values(
                cur,
                """
                INSERT INTO document_chunks (document_id, chunk_index, chunk_text, embedding, metadata)
                VALUES %s
                ON CONFLICT (document_id, chunk_index) DO UPDATE SET
                    chunk_text = EXCLUDED.chunk_text,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
                """,
                chunk_values,
            )
            
            conn.commit()
            return len(chunk_values)
    
    # =========================================================================
    # SQLite Catalog → documents table Migration
    # =========================================================================
    
    def migrate_sqlite_catalog(self, resume: bool = True) -> Dict[str, Any]:
        """
        Migrate SQLite document catalog to PostgreSQL.
        
        Args:
            resume: Whether to resume from checkpoint
            
        Returns:
            Migration statistics
        """
        migration_name = "sqlite_catalog"
        
        status = self.get_migration_status(migration_name)
        if status and status.status == 'completed':
            logger.info("SQLite catalog migration already completed")
            return {"status": "already_completed", "count": 0}
        
        if not self._sqlite_path or not os.path.exists(self._sqlite_path):
            return {"status": "skipped", "message": "SQLite path not found"}
        
        try:
            import sqlite3
        except ImportError:
            return {"status": "error", "message": "sqlite3 not available"}
        
        self.start_migration(migration_name)
        
        try:
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(self._sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            
            # Get total count
            cursor = sqlite_conn.execute("SELECT COUNT(*) FROM documents")
            total_count = cursor.fetchone()[0]
            logger.info(f"Found {total_count} documents in SQLite catalog")
            
            # Resume from checkpoint
            start_id = 0
            migrated_count = 0
            if resume and status and status.checkpoint:
                start_id = status.checkpoint.last_id
                migrated_count = status.checkpoint.count
            
            pg_conn = self._get_pg_connection()
            try:
                cursor = sqlite_conn.execute("""
                    SELECT * FROM documents 
                    WHERE rowid > ?
                    ORDER BY rowid
                """, (start_id,))
                
                batch = []
                last_rowid = start_id
                
                for row in cursor:
                    batch.append(dict(row))
                    last_rowid = row['rowid'] if 'rowid' in row.keys() else last_rowid + 1
                    
                    if len(batch) >= self.BATCH_SIZE_DOCUMENTS:
                        count = self._insert_document_batch(pg_conn, batch)
                        migrated_count += count
                        batch = []
                        
                        self.update_checkpoint(migration_name, MigrationCheckpoint(
                            phase='documents',
                            last_id=last_rowid,
                            count=migrated_count,
                        ))
                        logger.info(f"Migrated {migrated_count}/{total_count} documents")
                
                # Insert remaining batch
                if batch:
                    count = self._insert_document_batch(pg_conn, batch)
                    migrated_count += count
                
                self.complete_migration(migration_name)
                return {
                    "status": "completed",
                    "total": total_count,
                    "migrated": migrated_count,
                }
            finally:
                pg_conn.close()
                sqlite_conn.close()
                
        except Exception as e:
            self.fail_migration(migration_name, str(e))
            logger.error(f"SQLite migration failed: {e}")
            raise
    
    def _insert_document_batch(
        self,
        conn,
        documents: List[Dict[str, Any]],
    ) -> int:
        """Insert batch of documents into PostgreSQL."""
        values = []
        for doc in documents:
            # Map SQLite columns to PostgreSQL schema
            values.append((
                doc.get('hash') or doc.get('resource_hash'),
                doc.get('file_path', ''),
                doc.get('display_name') or doc.get('name', 'Unknown'),
                doc.get('source_type', 'unknown'),
                doc.get('url'),
                doc.get('suffix'),
                doc.get('size_bytes') or doc.get('size'),
                doc.get('original_path'),
                doc.get('base_path'),
                doc.get('relative_path'),
                doc.get('ingested_at'),
            ))
        
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO documents (
                    resource_hash, file_path, display_name, source_type,
                    url, suffix, size_bytes, original_path, base_path, 
                    relative_path, ingested_at
                )
                VALUES %s
                ON CONFLICT (resource_hash) DO UPDATE SET
                    display_name = COALESCE(EXCLUDED.display_name, documents.display_name),
                    url = COALESCE(EXCLUDED.url, documents.url)
                """,
                values,
            )
            conn.commit()
            return len(values)
    
    # =========================================================================
    # Conversation Schema Migration
    # =========================================================================
    
    def migrate_conversation_schema(
        self,
        config_to_model_map: Optional[Dict[int, Tuple[str, str]]] = None,
        resume: bool = True,
    ) -> Dict[str, Any]:
        """
        Migrate conversations from conf_id to model_used/pipeline_used.
        
        Args:
            config_to_model_map: Map of config_id → (model_name, pipeline_name)
                                 If None, attempts to auto-detect from configs table
            resume: Whether to resume from checkpoint
            
        Returns:
            Migration statistics
        """
        migration_name = "conversation_schema"
        
        status = self.get_migration_status(migration_name)
        if status and status.status == 'completed':
            logger.info("Conversation schema migration already completed")
            return {"status": "already_completed", "count": 0}
        
        self.start_migration(migration_name)
        
        try:
            conn = self._get_pg_connection()
            try:
                # Build config map if not provided
                if config_to_model_map is None:
                    config_to_model_map = self._build_config_map(conn)
                    logger.info(f"Auto-detected {len(config_to_model_map)} config mappings")
                
                # Resume from checkpoint
                start_id = 0
                migrated_count = 0
                if resume and status and status.checkpoint:
                    start_id = status.checkpoint.last_id
                    migrated_count = status.checkpoint.count
                
                # Get total count
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM conversations 
                        WHERE conf_id IS NOT NULL AND model_used IS NULL
                    """)
                    total_count = cur.fetchone()[0]
                
                logger.info(f"Found {total_count} conversations to migrate")
                
                # Migrate in batches
                while True:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT message_id, conf_id
                            FROM conversations
                            WHERE message_id > %s 
                              AND conf_id IS NOT NULL 
                              AND model_used IS NULL
                            ORDER BY message_id
                            LIMIT %s
                        """, (start_id, self.BATCH_SIZE_CONVERSATIONS))
                        
                        rows = cur.fetchall()
                        if not rows:
                            break
                        
                        # Build updates
                        updates = []
                        for message_id, conf_id in rows:
                            model, pipeline = config_to_model_map.get(conf_id, ('unknown', 'unknown'))
                            updates.append((model, pipeline, message_id))
                        
                        # Batch update
                        cur.executemany("""
                            UPDATE conversations 
                            SET model_used = %s, pipeline_used = %s
                            WHERE message_id = %s
                        """, updates)
                        
                        conn.commit()
                        
                        start_id = rows[-1][0]
                        migrated_count += len(rows)
                        
                        self.update_checkpoint(migration_name, MigrationCheckpoint(
                            phase='conversations',
                            last_id=start_id,
                            count=migrated_count,
                        ))
                        
                        logger.info(f"Migrated {migrated_count}/{total_count} conversations")
                
                # Also migrate ab_comparisons
                ab_migrated = self._migrate_ab_comparisons(conn, config_to_model_map)
                
                self.complete_migration(migration_name)
                return {
                    "status": "completed",
                    "conversations_migrated": migrated_count,
                    "ab_comparisons_migrated": ab_migrated,
                }
            finally:
                conn.close()
                
        except Exception as e:
            self.fail_migration(migration_name, str(e))
            logger.error(f"Conversation migration failed: {e}")
            raise
    
    def _build_config_map(self, conn) -> Dict[int, Tuple[str, str]]:
        """Build config_id → (model, pipeline) mapping from configs table."""
        config_map = {}
        
        with conn.cursor() as cur:
            cur.execute("SELECT config_id, config FROM configs")
            for config_id, config_json in cur.fetchall():
                try:
                    config = json.loads(config_json) if isinstance(config_json, str) else config_json
                    
                    # Extract model and pipeline from config
                    # Try various possible structures
                    model = (
                        config.get('model') or 
                        config.get('chat_model') or
                        config.get('llm', {}).get('model') or
                        'unknown'
                    )
                    pipeline = (
                        config.get('pipeline') or
                        config.get('pipeline_name') or
                        'QAPipeline'
                    )
                    
                    config_map[config_id] = (model, pipeline)
                except (json.JSONDecodeError, TypeError):
                    config_map[config_id] = ('unknown', 'unknown')
        
        return config_map
    
    def _migrate_ab_comparisons(
        self,
        conn,
        config_map: Dict[int, Tuple[str, str]],
    ) -> int:
        """Migrate ab_comparisons from config_id to model_a/model_b."""
        with conn.cursor() as cur:
            cur.execute("""
                SELECT comparison_id, config_a_id, config_b_id
                FROM ab_comparisons
                WHERE config_a_id IS NOT NULL 
                  AND model_a IS NULL
            """)
            rows = cur.fetchall()
            
            if not rows:
                return 0
            
            updates = []
            for comparison_id, config_a_id, config_b_id in rows:
                model_a, pipeline_a = config_map.get(config_a_id, ('unknown', 'unknown'))
                model_b, pipeline_b = config_map.get(config_b_id, ('unknown', 'unknown'))
                updates.append((model_a, pipeline_a, model_b, pipeline_b, comparison_id))
            
            cur.executemany("""
                UPDATE ab_comparisons
                SET model_a = %s, pipeline_a = %s, model_b = %s, pipeline_b = %s
                WHERE comparison_id = %s
            """, updates)
            
            conn.commit()
            return len(updates)
    
    # =========================================================================
    # Cleanup Operations
    # =========================================================================
    
    def drop_configs_table(self, backup: bool = True) -> Dict[str, Any]:
        """
        Drop the old configs table after verifying it's no longer needed.
        
        The configs table was used to store config snapshots per message.
        It often had massive duplication (73K+ rows with identical data).
        Now we track model_used/pipeline_used directly on conversations.
        
        Args:
            backup: If True, create a backup table before dropping
            
        Returns:
            Dictionary with operation status and stats
        """
        result = {
            'status': 'pending',
            'rows_backed_up': 0,
            'table_dropped': False,
        }
        
        conn = self._get_pg_connection()
        try:
            with conn.cursor() as cur:
                # Check if configs table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'configs'
                    )
                """)
                if not cur.fetchone()[0]:
                    result['status'] = 'skipped'
                    result['message'] = 'configs table does not exist'
                    return result
                
                # Count rows for reporting
                cur.execute("SELECT COUNT(*) FROM configs")
                row_count = cur.fetchone()[0]
                result['original_row_count'] = row_count
                
                # Check if any conversations still reference conf_id
                cur.execute("""
                    SELECT COUNT(*) FROM conversations 
                    WHERE conf_id IS NOT NULL AND model_used IS NULL
                """)
                unmigrated = cur.fetchone()[0]
                
                if unmigrated > 0:
                    result['status'] = 'blocked'
                    result['message'] = f'{unmigrated} conversations have conf_id but no model_used. Run migrate_conversation_schema first.'
                    return result
                
                # Create backup if requested
                if backup:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS configs_backup AS 
                        SELECT * FROM configs
                    """)
                    cur.execute("SELECT COUNT(*) FROM configs_backup")
                    result['rows_backed_up'] = cur.fetchone()[0]
                
                # Remove the foreign key constraint from conversations if it exists
                cur.execute("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'conversations' 
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name LIKE '%conf%'
                """)
                fk_constraints = cur.fetchall()
                for (constraint_name,) in fk_constraints:
                    cur.execute(f"ALTER TABLE conversations DROP CONSTRAINT IF EXISTS {constraint_name}")
                    result['dropped_constraints'] = result.get('dropped_constraints', []) + [constraint_name]
                
                # Drop the configs table
                cur.execute("DROP TABLE configs")
                result['table_dropped'] = True
                result['status'] = 'completed'
                
                conn.commit()
                logger.info(f"Dropped configs table ({row_count} rows, backup: {backup})")
                
        except Exception as e:
            conn.rollback()
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"Failed to drop configs table: {e}")
        finally:
            conn.close()
        
        return result
    
    def analyze_configs_table(self) -> Dict[str, Any]:
        """
        Analyze the configs table for duplication and usage.
        
        Returns:
            Dictionary with analysis results
        """
        result = {
            'exists': False,
            'total_rows': 0,
            'unique_configs': 0,
            'duplication_ratio': 0.0,
            'referenced_by_conversations': 0,
            'orphaned_configs': 0,
        }
        
        conn = self._get_pg_connection()
        try:
            with conn.cursor() as cur:
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'configs'
                    )
                """)
                if not cur.fetchone()[0]:
                    return result
                
                result['exists'] = True
                
                # Total rows
                cur.execute("SELECT COUNT(*) FROM configs")
                result['total_rows'] = cur.fetchone()[0]
                
                # Unique configs (by content hash)
                cur.execute("""
                    SELECT COUNT(DISTINCT MD5(
                        COALESCE(name, '') || 
                        COALESCE(pipeline, '') || 
                        COALESCE(chat_model::text, '') ||
                        COALESCE(condense_model::text, '')
                    ))
                    FROM configs
                """)
                result['unique_configs'] = cur.fetchone()[0]
                
                if result['total_rows'] > 0:
                    result['duplication_ratio'] = round(
                        result['total_rows'] / max(result['unique_configs'], 1), 1
                    )
                
                # Configs referenced by conversations
                cur.execute("""
                    SELECT COUNT(DISTINCT conf_id) 
                    FROM conversations 
                    WHERE conf_id IS NOT NULL
                """)
                result['referenced_by_conversations'] = cur.fetchone()[0]
                
                # Orphaned configs (not referenced)
                cur.execute("""
                    SELECT COUNT(*) FROM configs c
                    WHERE NOT EXISTS (
                        SELECT 1 FROM conversations conv WHERE conv.conf_id = c.conf_id
                    )
                """)
                result['orphaned_configs'] = cur.fetchone()[0]
                
        finally:
            conn.close()
        
        return result
    
    # =========================================================================
    # Full Migration
    # =========================================================================
    
    def run_full_migration(self) -> Dict[str, Any]:
        """
        Run all migrations in sequence.
        
        Returns:
            Combined migration statistics
        """
        results = {}
        
        # 1. Migrate ChromaDB vectors
        if self._chroma_path:
            logger.info("Starting ChromaDB migration...")
            results['chromadb'] = self.migrate_chromadb()
        
        # 2. Migrate SQLite catalog
        if self._sqlite_path:
            logger.info("Starting SQLite catalog migration...")
            results['sqlite_catalog'] = self.migrate_sqlite_catalog()
        
        # 3. Migrate conversation schema
        logger.info("Starting conversation schema migration...")
        results['conversation_schema'] = self.migrate_conversation_schema()
        
        return results


def run_migration_cli():
    """CLI entrypoint for running migrations."""
    import argparse
    
    parser = argparse.ArgumentParser(description='A2rchi PostgreSQL Migration Tool')
    parser.add_argument('--pg-host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--pg-port', type=int, default=5432, help='PostgreSQL port')
    parser.add_argument('--pg-database', default='a2rchi', help='PostgreSQL database')
    parser.add_argument('--pg-user', default='postgres', help='PostgreSQL user')
    parser.add_argument('--pg-password', default='', help='PostgreSQL password')
    parser.add_argument('--chroma-path', help='Path to ChromaDB persistence directory')
    parser.add_argument('--sqlite-path', help='Path to SQLite catalog database')
    parser.add_argument('--migration', choices=['chromadb', 'sqlite', 'conversations', 'all'],
                        default='all', help='Which migration to run')
    parser.add_argument('--no-resume', action='store_true', help='Start fresh, ignore checkpoints')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    pg_params = {
        'host': args.pg_host,
        'port': args.pg_port,
        'database': args.pg_database,
        'user': args.pg_user,
        'password': args.pg_password,
    }
    
    manager = MigrationManager(
        postgres_conn_params=pg_params,
        chroma_path=args.chroma_path,
        sqlite_path=args.sqlite_path,
    )
    
    resume = not args.no_resume
    
    if args.migration == 'chromadb':
        result = manager.migrate_chromadb(resume=resume)
    elif args.migration == 'sqlite':
        result = manager.migrate_sqlite_catalog(resume=resume)
    elif args.migration == 'conversations':
        result = manager.migrate_conversation_schema(resume=resume)
    else:
        result = manager.run_full_migration()
    
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    run_migration_cli()
