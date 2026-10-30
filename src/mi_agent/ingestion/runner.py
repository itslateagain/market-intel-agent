"""Ingestion orchestration: fetch -> persist raw payload -> parse -> append new rows to bronze.

Design points (the interview answers):
- Raw payloads are saved to a Unity Catalog Volume first, so any bronze row can be traced back
  to the exact bytes we received (lineage + reprocessing).
- Incremental: rows whose raw_id already exists in bronze are skipped, so re-running is safe.
- Failure isolation: one broken source is logged to pipeline_runs and does not stop the others.
"""
from __future__ import annotations

import logging
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..config import Settings
from .parsers import PARSERS, RawItem

log = logging.getLogger("mi_agent.ingestion")


def fetch_bytes(url: str, user_agent: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (https URLs from config)
        return r.read()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def run_ingestion(spark, settings: Settings, sources: dict, contact: str) -> dict:
    """Ingest every configured source once. Returns a summary dict."""
    from pyspark.sql import types as T

    run_id = "run_" + uuid.uuid4().hex[:12]
    ua = settings.ingestion.user_agent.format(contact=contact)
    bronze = settings.table("bronze_raw_items")
    raw_root = Path(f"/Volumes/{settings.catalog}/{settings.schema_}/{settings.raw_volume}")

    existing = {r.raw_id for r in spark.table(bronze).select("raw_id").collect()}
    summary = {"run_id": run_id, "sources": {}}
    run_rows: list[tuple] = []
    bronze_rows: list[tuple] = []

    for src in sources["sources"]:
        started, name = _now(), src["name"]
        status, err, n_in, n_new, dupes, rejected, path = "SUCCESS", None, 0, 0, 0, 0, None
        try:
            payload = fetch_bytes(src["url"], ua, settings.ingestion.request_timeout_seconds)
            ext = "json" if src["kind"] == "sec_edgar" else "xml"
            out_dir = raw_root / name
            out_dir.mkdir(parents=True, exist_ok=True)
            path = str(out_dir / f"{run_id}.{ext}")
            Path(path).write_bytes(payload)

            result = PARSERS[src["kind"]](payload, name, src["company"],
                                          settings.ingestion.max_items_per_source)
            n_in, rejected = len(result.items) + result.rejected, result.rejected
            seen_this_run: set[str] = set()
            for it in result.items:
                if it.raw_id in existing or it.raw_id in seen_this_run:
                    dupes += 1
                    continue
                seen_this_run.add(it.raw_id)
                bronze_rows.append(_bronze_row(it, path, started, run_id))
                n_new += 1
            if n_in == 0:
                status, err = "EMPTY", "source returned no parseable items"
        except Exception as e:  # noqa: BLE001  isolate per-source failures
            status, err = "FAILED", repr(e)[:500]
            log.exception("source %s failed", name)
        summary["sources"][name] = {"status": status, "parsed": n_in, "new": n_new,
                                    "duplicates": dupes, "rejected": rejected, "error": err}
        run_rows.append((run_id, f"ingest:{name}", started, _now(), status,
                         n_in, n_new, dupes, rejected, err))

    if bronze_rows:
        schema = T.StructType([
            T.StructField("raw_id", T.StringType(), False),
            T.StructField("source_name", T.StringType(), False),
            T.StructField("company", T.StringType(), False),
            T.StructField("item_url", T.StringType()), T.StructField("title", T.StringType()),
            T.StructField("body", T.StringType()), T.StructField("published_at", T.TimestampType()),
            T.StructField("content_hash", T.StringType()),
            T.StructField("raw_file_path", T.StringType()),
            T.StructField("ingested_at", T.TimestampType(), False),
            T.StructField("run_id", T.StringType(), False)])
        spark.createDataFrame(bronze_rows, schema).write.mode("append").saveAsTable(bronze)

    run_schema = ("run_id string, stage string, started_at timestamp, finished_at timestamp, "
                  "status string, records_in long, records_out long, duplicates_removed long, "
                  "rejected long, error string")
    spark.createDataFrame(run_rows, run_schema).write.mode("append").saveAsTable(
        settings.table("pipeline_runs"))
    return summary


def _bronze_row(it: RawItem, path: str, ingested_at: datetime, run_id: str) -> tuple:
    return (it.raw_id, it.source_name, it.company, it.item_url, it.title, it.body,
            it.published_at, it.content_hash, path, ingested_at, run_id)
