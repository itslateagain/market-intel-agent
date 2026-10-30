"""Typed settings loaded from config/settings.yaml. No secrets live here."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]


class Models(BaseModel):
    enrichment: str
    agent: str
    embedding: str


class AISearch(BaseModel):
    endpoint_name: str
    index_name: str


class Policy(BaseModel):
    min_importance_score: int = Field(ge=0, le=100)
    min_confidence: float = Field(ge=0, le=1)
    auto_approve_action_types: list[str] = []


class Ingestion(BaseModel):
    user_agent: str
    request_timeout_seconds: int = 20
    max_items_per_source: int = 50


class Settings(BaseModel):
    catalog: str
    schema_: str = Field(alias="schema")
    raw_volume: str
    models: Models
    ai_search: AISearch
    policy: Policy
    ingestion: Ingestion

    def table(self, name: str) -> str:
        """Fully qualified table name, e.g. workspace.market_intel.gold_events."""
        return f"{self.catalog}.{self.schema_}.{name}"


def load_settings(path: Path | None = None) -> Settings:
    path = path or ROOT / "config" / "settings.yaml"
    return Settings.model_validate(yaml.safe_load(path.read_text()))


def load_sources(path: Path | None = None) -> dict:
    path = path or ROOT / "config" / "sources.yaml"
    return yaml.safe_load(path.read_text())
