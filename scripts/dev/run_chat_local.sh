#!/bin/bash
# Run the chat app locally against the test database
# 
# Prerequisites:
#   1. Test database running: cd tests/smoke && docker compose -f docker-compose.integration.yaml up -d
#   2. Python environment with dependencies installed
#
# Usage:
#   ./scripts/dev/run_chat_local.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo "📦 Activating virtual environment..."
    source "$PROJECT_ROOT/.venv/bin/activate"
elif [ -d "$PROJECT_ROOT/venv" ]; then
    echo "📦 Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Configuration directory
CONFIG_DIR="${PROJECT_ROOT}/tests/smoke/local_dev_config"
mkdir -p "$CONFIG_DIR"

# Create config file if it doesn't exist
CONFIG_FILE="$CONFIG_DIR/local-dev.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'EOF'
# Local development config for running chat app against test database
name: local-dev

global:
  DATA_PATH: /tmp/a2rchi-data/
  ACCOUNTS_PATH: /tmp/a2rchi-accounts/
  verbosity: 2

services:
  postgres:
    host: localhost
    port: 5439
    database: a2rchi
    user: a2rchi
  chat_app:
    host: "0.0.0.0"
    hostname: localhost
    port: 2786
    external_port: 2786
    # These will be filled in by the script
    template_folder: "PLACEHOLDER"
    static_folder: "PLACEHOLDER"
    num_responses_until_feedback: 5
    auth:
      enabled: false

a2rchi:
  agent_description: "Local development test agent"
  model_class_map:
    openai: gpt-4o-mini
    ollama: llama3.2
    anthropic: claude-3-5-sonnet-20241022
  providers:
    - type: openai
      name: OpenAI
      api_key_secret: OPENAI_API_KEY
      models:
        - model: gpt-4o-mini
          display_name: GPT-4o Mini
  pipelines:
    - name: main
      condense: null
      respond: null
      insert: null
      remove: null
      model: openai
  pipeline_map:
    condense: main
    respond: main
    insert: main
    remove: main
EOF
    echo "Created config file: $CONFIG_FILE"
fi

# Update template/static paths in config
sed -i.bak "s|template_folder:.*|template_folder: \"${PROJECT_ROOT}/src/interfaces/chat_app/templates\"|" "$CONFIG_FILE"
sed -i.bak "s|static_folder:.*|static_folder: \"${PROJECT_ROOT}/src/interfaces/chat_app/static\"|" "$CONFIG_FILE"
rm -f "$CONFIG_FILE.bak"

# Create directories
mkdir -p /tmp/a2rchi-data /tmp/a2rchi-accounts

# Check if test database is running
if ! docker ps --format "{{.Names}}" | grep -q "a2rchi-test-postgres"; then
    echo "❌ Test database not running!"
    echo "   Start it with:"
    echo "   cd tests/smoke && docker compose -f docker-compose.integration.yaml up -d"
    exit 1
fi
echo "✅ Test database is running"

# Set environment variables
export A2RCHI_CONFIGS_PATH="$CONFIG_DIR/"
export PG_PASSWORD=testpassword123

# Check for optional API keys
if [ -n "${OPENAI_API_KEY:-}" ]; then
    echo "✅ OPENAI_API_KEY is set"
else
    echo "⚠️  OPENAI_API_KEY not set - LLM features won't work"
fi

echo ""
echo "Starting chat app..."
echo "  Config: $CONFIG_FILE"
echo "  Database: localhost:5439"
echo "  Chat UI: http://localhost:2786"
echo "  Python: $(which python)"
echo ""

# Run the chat service
cd "$PROJECT_ROOT"
python src/bin/service_chat.py
