-- Run via notebooks/01_setup.py. Idempotent. {catalog}/{schema} are substituted from settings.yaml.
CREATE SCHEMA IF NOT EXISTS {catalog}.{schema};
CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.raw;

-- BRONZE: append-only raw items, exactly as fetched, with lineage back to the source.
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.bronze_raw_items (
  raw_id        STRING NOT NULL COMMENT 'sha256(source_name|item_url|content_hash) prefix',
  source_name   STRING NOT NULL,
  company       STRING NOT NULL,
  item_url      STRING,
  title         STRING,
  body          STRING,
  published_at  TIMESTAMP,
  content_hash  STRING,
  raw_file_path STRING COMMENT 'UC Volume path of the raw payload',
  ingested_at   TIMESTAMP NOT NULL,
  run_id        STRING NOT NULL
) COMMENT 'Raw ingested items. Never updated.';

-- SILVER: cleaned, validated, deduplicated. One row per event_id.
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.silver_events (
  event_id      STRING NOT NULL,
  company       STRING NOT NULL,
  title         STRING NOT NULL,
  body          STRING,
  source_url    STRING NOT NULL,
  source_name   STRING NOT NULL,
  published_at  TIMESTAMP,
  ingested_at   TIMESTAMP NOT NULL,
  content_hash  STRING,
  first_raw_id  STRING COMMENT 'lineage to bronze_raw_items.raw_id'
);

-- GOLD: enriched + agent-analysed. Change Data Feed on, because the AI Search
-- Delta Sync index on a standard endpoint requires it.
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.gold_events (
  event_id            STRING NOT NULL,
  company             STRING NOT NULL,
  event_type          STRING,
  title               STRING NOT NULL,
  event_summary       STRING,
  source_url          STRING NOT NULL,
  source_name         STRING NOT NULL,
  published_at        TIMESTAMP,
  ingested_at         TIMESTAMP NOT NULL,
  products            ARRAY<STRING>,
  technologies        ARRAY<STRING>,
  themes              ARRAY<STRING>,
  importance_score    INT,
  confidence_score    DOUBLE,
  potential_impact    STRING,
  evidence            STRING,
  agent_recommendation STRING,
  agent_action        STRING,
  action_status       STRING,
  search_text         STRING COMMENT 'text that gets embedded by AI Search'
) TBLPROPERTIES (delta.enableChangeDataFeed = true);

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.company_profiles (
  company STRING NOT NULL, description STRING, focus_areas ARRAY<STRING>, updated_at TIMESTAMP
);

-- Observability and audit.
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.pipeline_runs (
  run_id STRING NOT NULL, stage STRING NOT NULL, started_at TIMESTAMP, finished_at TIMESTAMP,
  status STRING, records_in BIGINT, records_out BIGINT, duplicates_removed BIGINT,
  rejected BIGINT, error STRING
);

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.dq_results (
  run_id STRING, check_name STRING, table_name STRING, passed BOOLEAN,
  failing_rows BIGINT, checked_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.agent_runs (
  agent_run_id STRING NOT NULL, event_id STRING NOT NULL, model STRING,
  retrieved_event_ids ARRAY<STRING>, decision_json STRING, policy_reason STRING,
  latency_ms BIGINT, status STRING, error STRING, created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.actions (
  action_id STRING NOT NULL, event_id STRING NOT NULL, action_type STRING NOT NULL,
  recommended_by STRING, approved_by STRING, executed_at TIMESTAMP,
  status STRING, output STRING, created_at TIMESTAMP
);
