"""Contracts between pipeline stages. The agent's output is validated against AgentDecision."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EventType(str, Enum):
    PRODUCT_LAUNCH = "PRODUCT_LAUNCH"
    AI_CAPABILITY = "AI_CAPABILITY"
    ACQUISITION = "ACQUISITION"
    PARTNERSHIP = "PARTNERSHIP"
    PRICING_CHANGE = "PRICING_CHANGE"
    MAJOR_RELEASE = "MAJOR_RELEASE"
    POSITIONING_CHANGE = "POSITIONING_CHANGE"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    FINANCIAL_FILING = "FINANCIAL_FILING"
    OTHER = "OTHER"


class AgentDecision(BaseModel):
    """Structured agent output. reasoning_summary is a short, evidence-tied rationale,
    not chain-of-thought."""
    classification: EventType
    importance_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    summary: str
    reasoning_summary: str
    potential_impact: str
    recommended_action: str
    supporting_event_ids: list[str] = []


class ActionStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class ActionRecord(BaseModel):
    action_id: str
    event_id: str
    action_type: str
    recommended_by: str            # model endpoint name
    approved_by: str | None = None  # human identity; None until approved
    executed_at: datetime | None = None
    status: ActionStatus = ActionStatus.PROPOSED
    output: str | None = None
