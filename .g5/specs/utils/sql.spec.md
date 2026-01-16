---
spec_id: utils/sql
type: module
source_files:
  - src/utils/sql.py
test_file: null
status: extracted
---

# SQL Query Constants

> ⚠️ **AUTO-GENERATED FROM CODE**: Review for accuracy.

## Overview

SQL query templates used by A2rchi for database operations. All queries use parameterized placeholders (`%s`) for PostgreSQL.

## Structured Design Doc

### Constants

#### Conversation Queries

- `SQL_INSERT_CONVO` - Insert conversation message, returns `message_id`
- `SQL_QUERY_CONVO` - Query conversation history by ID
- `SQL_QUERY_CONVO_WITH_FEEDBACK` - Query conversation with feedback status
- `SQL_CREATE_CONVERSATION` - Create new conversation metadata
- `SQL_UPDATE_CONVERSATION_TIMESTAMP` - Update last_message_at
- `SQL_LIST_CONVERSATIONS` - List conversations for a client
- `SQL_GET_CONVERSATION_METADATA` - Get single conversation metadata
- `SQL_DELETE_CONVERSATION` - Delete conversation by ID and client

#### Config Queries

- `SQL_INSERT_CONFIG` - Insert configuration, returns `config_id`

#### Feedback Queries

- `SQL_INSERT_FEEDBACK` - Insert feedback for a message
- `SQL_DELETE_REACTION_FEEDBACK` - Delete like/dislike feedback

#### Timing Queries

- `SQL_INSERT_TIMING` - Insert timing metrics for a message

#### Agent Tool Calls

- `SQL_INSERT_TOOL_CALLS` - Insert agent tool call records
- `SQL_QUERY_TOOL_CALLS` - Query tool calls for a message

## Guardrails

- All queries use parameterized placeholders - no string interpolation
- Expects PostgreSQL database
- Uses `psycopg2`-style `%s` placeholders

## Testing Contracts

- Queries are valid SQL syntax
- All placeholders are positional (%s)
