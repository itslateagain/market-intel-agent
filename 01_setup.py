# Databricks notebook source
# MAGIC %md
# MAGIC # 01 Setup: create schema, volume and tables
# MAGIC Requires the repo to be in your workspace (see README). Run all on serverless compute.

# COMMAND ----------
import os
import sys

# Repo root = parent of this notebooks/ folder.
REPO_ROOT = os.path.dirname(os.getcwd())
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))
%pip install --quiet pydantic pyyaml feedparser

# COMMAND ----------
from pathlib import Path

from mi_agent.config import load_settings

s = load_settings(Path(REPO_ROOT) / "config" / "settings.yaml")
ddl = (Path(REPO_ROOT) / "sql" / "00_setup.sql").read_text()
for stmt in [x.strip() for x in ddl.split(";") if x.strip()]:
    lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
    sql = "\n".join(lines).strip().format(catalog=s.catalog, schema=s.schema_)
    if sql:
        spark.sql(sql)

display(spark.sql(f"SHOW TABLES IN {s.catalog}.{s.schema_}"))
