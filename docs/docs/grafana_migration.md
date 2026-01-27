# Grafana Dashboard Migration Guide

This guide shows how to migrate existing Grafana dashboards from the old schema 
(using `configs` table joins) to the new PostgreSQL-consolidated schema (using 
`model_used` column directly in `conversations`).

## Schema Changes Summary

### Old Schema
```sql
-- Conversations referenced configs table via foreign key
SELECT c.*, cf.config_name 
FROM conversations c
JOIN configs cf ON c.conf_id = cf.config_id
WHERE cf.config_name = 'production';
```

### New Schema (V2)
```sql
-- Model info stored directly in conversations table
SELECT * FROM conversations 
WHERE model_used = 'gpt-4o' 
  AND pipeline_used = 'QAPipeline';
```

## Query Migration Examples

### 1. Conversation Count by Model

**Old Query:**
```sql
SELECT 
    cf.config_name,
    COUNT(*) as message_count
FROM conversations c
JOIN configs cf ON c.conf_id = cf.config_id
WHERE c.ts >= NOW() - INTERVAL '7 days'
GROUP BY cf.config_name
ORDER BY message_count DESC;
```

**New Query:**
```sql
SELECT 
    model_used,
    COUNT(*) as message_count
FROM conversations
WHERE ts >= NOW() - INTERVAL '7 days'
  AND model_used IS NOT NULL
GROUP BY model_used
ORDER BY message_count DESC;
```

### 2. Response Time by Model

**Old Query:**
```sql
SELECT 
    cf.config_name,
    AVG(t.chain_finished_ts - t.server_received_msg_ts) as avg_response_time
FROM timings t
JOIN conversations c ON t.msg_id = c.message_id
JOIN configs cf ON c.conf_id = cf.config_id
WHERE t.server_received_msg_ts >= NOW() - INTERVAL '24 hours'
GROUP BY cf.config_name;
```

**New Query:**
```sql
SELECT 
    c.model_used,
    AVG(t.chain_finished_ts - t.server_received_msg_ts) as avg_response_time
FROM timings t
JOIN conversations c ON t.msg_id = c.message_id
WHERE t.server_received_msg_ts >= NOW() - INTERVAL '24 hours'
  AND c.model_used IS NOT NULL
GROUP BY c.model_used;
```

### 3. Pipeline Performance Comparison

**New Query (no equivalent in old schema):**
```sql
SELECT 
    pipeline_used,
    COUNT(*) as total_messages,
    AVG(EXTRACT(EPOCH FROM (t.chain_finished_ts - t.server_received_msg_ts))) as avg_seconds
FROM conversations c
JOIN timings t ON t.msg_id = c.message_id
WHERE c.ts >= NOW() - INTERVAL '7 days'
  AND c.pipeline_used IS NOT NULL
GROUP BY pipeline_used
ORDER BY total_messages DESC;
```

### 4. Model Usage Over Time (Time Series)

**New Query:**
```sql
SELECT 
    time_bucket('1 hour', ts) as time,
    model_used,
    COUNT(*) as count
FROM conversations
WHERE ts >= NOW() - INTERVAL '24 hours'
  AND model_used IS NOT NULL
GROUP BY time, model_used
ORDER BY time;
```

### 5. A/B Comparison Results

**Old Query:**
```sql
SELECT 
    cf_a.config_name as model_a,
    cf_b.config_name as model_b,
    ab.preference,
    COUNT(*) as count
FROM ab_comparisons ab
JOIN configs cf_a ON ab.config_id_a = cf_a.config_id
JOIN configs cf_b ON ab.config_id_b = cf_b.config_id
WHERE ab.created_at >= NOW() - INTERVAL '7 days'
GROUP BY cf_a.config_name, cf_b.config_name, ab.preference;
```

**New Query:**
```sql
SELECT 
    model_a,
    model_b,
    preference,
    COUNT(*) as count
FROM ab_comparisons
WHERE created_at >= NOW() - INTERVAL '7 days'
  AND model_a IS NOT NULL
GROUP BY model_a, model_b, preference;
```

### 6. Feedback by Model

**New Query:**
```sql
SELECT 
    c.model_used,
    f.feedback_type,
    COUNT(*) as count
FROM feedback f
JOIN conversations c ON f.msg_id = c.message_id
WHERE f.created_at >= NOW() - INTERVAL '7 days'
  AND c.model_used IS NOT NULL
GROUP BY c.model_used, f.feedback_type
ORDER BY c.model_used, count DESC;
```

### 7. User Preference Distribution

**New Query:**
```sql
SELECT 
    u.preferred_model,
    COUNT(DISTINCT u.id) as user_count,
    COUNT(c.message_id) as message_count
FROM users u
LEFT JOIN conversations c ON c.service = u.id  -- Assuming service stores user_id
WHERE u.preferred_model IS NOT NULL
GROUP BY u.preferred_model
ORDER BY user_count DESC;
```

### 8. Cost Estimation by Model (Token Tracking)

**New Query (requires token columns if added):**
```sql
-- Example if input_tokens/output_tokens columns are added
SELECT 
    model_used,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    -- Estimated cost calculation
    CASE model_used
        WHEN 'gpt-4o' THEN SUM(input_tokens) * 0.0025 / 1000 + SUM(output_tokens) * 0.01 / 1000
        WHEN 'gpt-4o-mini' THEN SUM(input_tokens) * 0.00015 / 1000 + SUM(output_tokens) * 0.0006 / 1000
        WHEN 'claude-3-5-sonnet' THEN SUM(input_tokens) * 0.003 / 1000 + SUM(output_tokens) * 0.015 / 1000
        ELSE 0
    END as estimated_cost_usd
FROM conversations
WHERE ts >= NOW() - INTERVAL '30 days'
  AND model_used IS NOT NULL
GROUP BY model_used
ORDER BY total_input_tokens DESC;
```

## Grafana Dashboard JSON Snippets

### Panel: Model Usage Pie Chart

```json
{
  "datasource": {
    "type": "postgres",
    "uid": "${DS_POSTGRESQL}"
  },
  "targets": [
    {
      "format": "table",
      "group": [],
      "rawQuery": true,
      "rawSql": "SELECT model_used as \"Model\", COUNT(*) as \"Messages\" FROM conversations WHERE ts >= $__timeFrom() AND ts <= $__timeTo() AND model_used IS NOT NULL GROUP BY model_used ORDER BY \"Messages\" DESC",
      "refId": "A"
    }
  ],
  "type": "piechart",
  "title": "Model Usage Distribution"
}
```

### Panel: Response Time by Model (Time Series)

```json
{
  "datasource": {
    "type": "postgres",
    "uid": "${DS_POSTGRESQL}"
  },
  "targets": [
    {
      "format": "time_series",
      "rawQuery": true,
      "rawSql": "SELECT time_bucket('1 hour', t.server_received_msg_ts) as time, c.model_used as metric, AVG(EXTRACT(EPOCH FROM (t.chain_finished_ts - t.server_received_msg_ts))) as value FROM timings t JOIN conversations c ON t.msg_id = c.message_id WHERE t.server_received_msg_ts >= $__timeFrom() AND t.server_received_msg_ts <= $__timeTo() AND c.model_used IS NOT NULL GROUP BY time, c.model_used ORDER BY time",
      "refId": "A"
    }
  ],
  "type": "timeseries",
  "title": "Average Response Time by Model"
}
```

### Panel: A/B Comparison Results

```json
{
  "datasource": {
    "type": "postgres",
    "uid": "${DS_POSTGRESQL}"
  },
  "targets": [
    {
      "format": "table",
      "rawQuery": true,
      "rawSql": "SELECT model_a || ' vs ' || model_b as \"Comparison\", SUM(CASE WHEN preference = 'A' THEN 1 ELSE 0 END) as \"Prefer A\", SUM(CASE WHEN preference = 'B' THEN 1 ELSE 0 END) as \"Prefer B\", SUM(CASE WHEN preference = 'tie' THEN 1 ELSE 0 END) as \"Tie\", COUNT(*) as \"Total\" FROM ab_comparisons WHERE created_at >= $__timeFrom() AND created_at <= $__timeTo() AND model_a IS NOT NULL GROUP BY model_a, model_b ORDER BY \"Total\" DESC",
      "refId": "A"
    }
  ],
  "type": "table",
  "title": "A/B Comparison Results"
}
```

## Variable Templates

### Model Dropdown Variable

```json
{
  "name": "model",
  "label": "Model",
  "type": "query",
  "query": "SELECT DISTINCT model_used FROM conversations WHERE model_used IS NOT NULL ORDER BY model_used",
  "multi": true,
  "includeAll": true
}
```

### Pipeline Dropdown Variable

```json
{
  "name": "pipeline",
  "label": "Pipeline",
  "type": "query",
  "query": "SELECT DISTINCT pipeline_used FROM conversations WHERE pipeline_used IS NOT NULL ORDER BY pipeline_used",
  "multi": true,
  "includeAll": true
}
```

## Read-Only User Setup

The init-v2.sql already creates a read-only user for Grafana:

```sql
-- Created by init-v2.sql
CREATE USER grafana_reader WITH PASSWORD 'your_secure_password';
GRANT CONNECT ON DATABASE a2rchi TO grafana_reader;
GRANT USAGE ON SCHEMA public TO grafana_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO grafana_reader;
```

Configure your Grafana PostgreSQL datasource with:
- Host: `postgres:5432` (or your PostgreSQL host)
- Database: `a2rchi`
- User: `grafana_reader`
- SSL Mode: As appropriate for your environment
