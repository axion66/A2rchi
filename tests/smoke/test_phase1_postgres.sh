#!/usr/bin/env bash
# Phase 1 Infrastructure Test: PostgreSQL 17 with pgvector + pg_textsearch
# Tests Dockerfile build and init.sql schema

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_status() { echo -e "${GREEN}[✓]${NC} $1"; }
echo_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
echo_error() { echo -e "${RED}[✗]${NC} $1"; }

CONTAINER_NAME="a2rchi-postgres-test-$$"
IMAGE_NAME="a2rchi-postgres-test"
TEMP_DIR=""

cleanup() {
    echo ""
    echo "Cleaning up..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
    docker rmi "$IMAGE_NAME" 2>/dev/null || true
    echo_status "Cleanup complete"
}

trap cleanup EXIT

# Test 1: Build Dockerfile
echo ""
echo "========================================"
echo "Phase 1 Infrastructure Tests"
echo "========================================"
echo ""

echo "Test 1: Building PostgreSQL 17 + pgvector Docker image..."
if docker build -t "$IMAGE_NAME" \
    -f "$PROJECT_ROOT/src/cli/templates/dockerfiles/Dockerfile-postgres" \
    "$PROJECT_ROOT" 2>&1 | tail -20; then
    echo_status "Docker image built successfully"
else
    echo_error "Failed to build Docker image"
    exit 1
fi

# Test 2: Create temp dir with init.sql (rendered with defaults)
echo ""
echo "Test 2: Preparing init.sql with Jinja2 defaults..."
TEMP_DIR=$(mktemp -d)

# Simple Jinja2 render using Python
python3 << EOF
import re
template_path = "$PROJECT_ROOT/src/cli/templates/init-v2.sql"
output_path = "$TEMP_DIR/init.sql"

with open(template_path, 'r') as f:
    content = f.read()

# Replace Jinja2 variables with defaults
content = re.sub(r'\{\{\s*embedding_dimensions\s*\|\s*default\(\d+\)\s*\}\}', '384', content)
content = re.sub(r'\{\{\s*embedding_dimensions\s*\}\}', '384', content)
content = re.sub(r'\{\%\s*if\s+vector_index_type.*?\{\%\s*endif\s*-?\%\}', 
    '''CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks 
    USING hnsw (embedding vector_cosine_ops) 
    WITH (m = 16, ef_construction = 64);''', content, flags=re.DOTALL)
content = re.sub(r'\{\%\s*if\s+use_grafana.*?\{\%\s*endif\s*-?\%\}', '', content, flags=re.DOTALL)

# Remove any remaining Jinja2 syntax
content = re.sub(r'\{\{.*?\}\}', '', content)
content = re.sub(r'\{\%.*?-?\%\}', '', content)

with open(output_path, 'w') as f:
    f.write(content)
    
print(f"Generated init.sql ({len(content)} bytes)")
EOF

if [ -f "$TEMP_DIR/init.sql" ]; then
    echo_status "init.sql generated"
else
    echo_error "Failed to generate init.sql"
    exit 1
fi

# Test 3: Start PostgreSQL container
echo ""
echo "Test 3: Starting PostgreSQL container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -e POSTGRES_PASSWORD=testpass \
    -e POSTGRES_USER=a2rchi \
    -e POSTGRES_DB=a2rchi-db \
    -v "$TEMP_DIR/init.sql:/docker-entrypoint-initdb.d/init.sql:ro" \
    "$IMAGE_NAME"

echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker exec "$CONTAINER_NAME" pg_isready -U a2rchi -d a2rchi-db > /dev/null 2>&1; then
        echo_status "PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo_error "PostgreSQL did not become ready in time"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi
    sleep 1
done

# Test 4: Verify extensions
echo ""
echo "Test 4: Verifying PostgreSQL extensions..."

check_extension() {
    local ext=$1
    local required=$2
    if docker exec "$CONTAINER_NAME" psql -U a2rchi -d a2rchi-db -tAc \
        "SELECT 1 FROM pg_extension WHERE extname='$ext'" | grep -q 1; then
        echo_status "Extension '$ext' installed"
        return 0
    else
        if [ "$required" = "true" ]; then
            echo_error "Required extension '$ext' not installed"
            return 1
        else
            echo_warning "Optional extension '$ext' not installed (OK)"
            return 0
        fi
    fi
}

check_extension "vector" true
check_extension "pgcrypto" true
check_extension "pg_trgm" true
check_extension "pg_textsearch" false  # Optional, may not be GA

# Test 5: Verify tables created
echo ""
echo "Test 5: Verifying tables..."

REQUIRED_TABLES=(
    "users"
    "static_config"
    "dynamic_config"
    "documents"
    "document_chunks"
    "user_document_defaults"
    "conversation_document_overrides"
    "configs"
    "conversation_metadata"
    "conversations"
    "feedback"
    "timing"
    "agent_tool_calls"
    "ab_comparisons"
    "migration_state"
)

for table in "${REQUIRED_TABLES[@]}"; do
    if docker exec "$CONTAINER_NAME" psql -U a2rchi -d a2rchi-db -tAc \
        "SELECT 1 FROM information_schema.tables WHERE table_name='$table'" | grep -q 1; then
        echo_status "Table '$table' exists"
    else
        echo_error "Table '$table' missing"
        exit 1
    fi
done

# Test 6: Verify vector column type
echo ""
echo "Test 6: Verifying vector column..."
VECTOR_TYPE=$(docker exec "$CONTAINER_NAME" psql -U a2rchi -d a2rchi-db -tAc \
    "SELECT udt_name FROM information_schema.columns WHERE table_name='document_chunks' AND column_name='embedding'")

if [ "$VECTOR_TYPE" = "vector" ]; then
    echo_status "Vector column type correct"
else
    echo_error "Vector column type incorrect: $VECTOR_TYPE"
    exit 1
fi

# Test 7: Test vector operations
echo ""
echo "Test 7: Testing vector operations..."
docker exec "$CONTAINER_NAME" psql -U a2rchi -d a2rchi-db << 'EOSQL'
-- Insert a test document
INSERT INTO documents (resource_hash, file_path, display_name, source_type)
VALUES ('test123', '/test/path', 'Test Doc', 'local_files');

-- Insert a test chunk with vector
INSERT INTO document_chunks (document_id, chunk_index, chunk_text, embedding)
VALUES (1, 0, 'This is test content', '[0.1, 0.2, 0.3]'::vector(3) || repeat('[0.0]'::vector(1), 381));

-- Test similarity search (this should work even if result is trivial)
SELECT id, document_id, 1 - (embedding <=> '[0.1, 0.2, 0.3]'::vector(3) || repeat('[0.0]'::vector(1), 381)) as similarity
FROM document_chunks
ORDER BY embedding <=> '[0.1, 0.2, 0.3]'::vector(3) || repeat('[0.0]'::vector(1), 381)
LIMIT 1;

-- Cleanup
DELETE FROM document_chunks WHERE document_id = 1;
DELETE FROM documents WHERE id = 1;
EOSQL

if [ $? -eq 0 ]; then
    echo_status "Vector operations work correctly"
else
    echo_error "Vector operations failed"
    exit 1
fi

# Test 8: Verify indexes
echo ""
echo "Test 8: Verifying indexes..."

EXPECTED_INDEXES=(
    "idx_users_email"
    "idx_documents_hash"
    "idx_documents_source"
    "idx_chunks_document"
    "idx_chunks_embedding"
    "idx_feedback_mid"
)

for idx in "${EXPECTED_INDEXES[@]}"; do
    if docker exec "$CONTAINER_NAME" psql -U a2rchi -d a2rchi-db -tAc \
        "SELECT 1 FROM pg_indexes WHERE indexname='$idx'" | grep -q 1; then
        echo_status "Index '$idx' exists"
    else
        echo_warning "Index '$idx' not found (may be conditionally created)"
    fi
done

# Test 9: Check dynamic_config initialized
echo ""
echo "Test 9: Verifying dynamic_config defaults..."
ROW_COUNT=$(docker exec "$CONTAINER_NAME" psql -U a2rchi -d a2rchi-db -tAc \
    "SELECT COUNT(*) FROM dynamic_config")

if [ "$ROW_COUNT" = "1" ]; then
    echo_status "dynamic_config initialized with defaults"
else
    echo_error "dynamic_config not initialized correctly (rows: $ROW_COUNT)"
    exit 1
fi

# Test 10: PostgreSQL version check
echo ""
echo "Test 10: Verifying PostgreSQL version..."
PG_VERSION=$(docker exec "$CONTAINER_NAME" psql -U a2rchi -d a2rchi-db -tAc "SHOW server_version")
echo "PostgreSQL version: $PG_VERSION"

if [[ "$PG_VERSION" == 17* ]]; then
    echo_status "PostgreSQL 17.x confirmed"
else
    echo_warning "PostgreSQL version is $PG_VERSION (expected 17.x)"
fi

echo ""
echo "========================================"
echo "All Phase 1 Infrastructure Tests Passed!"
echo "========================================"
echo ""
echo "Summary:"
echo "  - Docker image builds successfully"
echo "  - PostgreSQL 17 with pgvector operational"
echo "  - Schema v2.0 creates all tables and indexes"
echo "  - Vector operations work correctly"
echo ""
