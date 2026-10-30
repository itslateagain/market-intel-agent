# Databricks notebook source
# MAGIC %md
# MAGIC # 02 Ingest: fetch real feeds into bronze
# MAGIC Run all on serverless. Safe to re-run: already-seen items are skipped.
# MAGIC First time only: store your contact email as a secret (SEC requires a real contact in the
# MAGIC User-Agent, and we never commit it). Run the next cell once.

# COMMAND ----------
# One-time. Replace the value, run this cell once, then delete the value from the cell.
# from databricks.sdk import WorkspaceClient
# WorkspaceClient().secrets.put_secret(scope="mi-agent", key="contact_email", string_value="YOUR_EMAIL")

# COMMAND ----------
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.getcwd()), "src"))
%pip install --quiet pydantic pyyaml feedparser

# COMMAND ----------
import json
from pathlib import Path

from mi_agent.config import load_settings, load_sources
from mi_agent.ingestion.runner import run_ingestion

root = Path(os.path.dirname(os.getcwd()))
settings = load_settings(root / "config" / "settings.yaml")
sources = load_sources(root / "config" / "sources.yaml")
contact = dbutils.secrets.get("mi-agent", "contact_email")

summary = run_ingestion(spark, settings, sources, contact)
print(json.dumps(summary, indent=2))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Proof: what landed in bronze

# COMMAND ----------
b = settings.table("bronze_raw_items")
display(spark.sql(f"SELECT source_name, count(*) AS rows, max(published_at) AS newest FROM {b} GROUP BY 1 ORDER BY 1"))
display(spark.sql(f"SELECT source_name, company, title, item_url, published_at FROM {b} ORDER BY ingested_at DESC, published_at DESC LIMIT 15"))
display(spark.sql(f"SELECT stage, status, records_in, records_out, duplicates_removed, rejected, error FROM {settings.table('pipeline_runs')} ORDER BY started_at DESC LIMIT 12"))
