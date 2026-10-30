# AI Market Intelligence Agent (Databricks)

Work in progress. Monitors public company feeds, turns them into structured intelligence
(bronze → silver → gold), grounds an AI agent in historical context, and proposes
human-approved actions with a full audit trail. Built on Databricks Free Edition.

## Layout
- `config/`: settings (thresholds, models) and sources. No secrets.
- `src/mi_agent/`: typed, unit-tested modules (ids, config, models, policy; more per phase)
- `sql/`: DDL for bronze, silver, gold, audit and observability tables
- `notebooks/`: thin Databricks entry points that call `src/`
- `tests/`: pytest suite (`pip install -e .[dev] && pytest`)

## Status
Phase 1 (skeleton) complete. Next: ingestion.
