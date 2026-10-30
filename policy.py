"""Policy gate between the agent's decision and any action. Pure function, easy to test."""
from __future__ import annotations

from dataclasses import dataclass

from .config import Policy
from .models import AgentDecision


@dataclass(frozen=True)
class PolicyResult:
    propose_action: bool
    requires_human_approval: bool
    reason: str


def evaluate(decision: AgentDecision, policy: Policy, action_type: str) -> PolicyResult:
    """Propose an action only if BOTH thresholds are met. Approval is required unless the
    action type is explicitly allow-listed (empty by default)."""
    if decision.importance_score < policy.min_importance_score:
        return PolicyResult(False, False,
                            f"importance {decision.importance_score} < {policy.min_importance_score}")
    if decision.confidence < policy.min_confidence:
        return PolicyResult(False, False,
                            f"confidence {decision.confidence} < {policy.min_confidence}")
    needs_human = action_type not in policy.auto_approve_action_types
    return PolicyResult(True, needs_human, "thresholds met")
