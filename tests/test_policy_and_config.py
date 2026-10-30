import pytest
from pydantic import ValidationError

from mi_agent.config import Policy, load_settings, load_sources
from mi_agent.models import AgentDecision
from mi_agent.policy import evaluate


def _decision(score=85, conf=0.9):
    return AgentDecision(classification="PRODUCT_LAUNCH", importance_score=score, confidence=conf,
                         summary="s", reasoning_summary="r", potential_impact="i",
                         recommended_action="brief")


POLICY = Policy(min_importance_score=70, min_confidence=0.75)


def test_proposes_when_both_thresholds_met_and_requires_human():
    r = evaluate(_decision(), POLICY, "intelligence_alert")
    assert r.propose_action and r.requires_human_approval


def test_blocks_low_importance_or_low_confidence():
    assert not evaluate(_decision(score=50), POLICY, "intelligence_alert").propose_action
    assert not evaluate(_decision(conf=0.5), POLICY, "intelligence_alert").propose_action


def test_allow_list_skips_approval_only_for_listed_types():
    p = Policy(min_importance_score=70, min_confidence=0.75, auto_approve_action_types=["log_only"])
    assert not evaluate(_decision(), p, "log_only").requires_human_approval
    assert evaluate(_decision(), p, "intelligence_alert").requires_human_approval


def test_agent_decision_rejects_bad_output():
    with pytest.raises(ValidationError):
        _decision(score=150)
    with pytest.raises(ValidationError):
        AgentDecision(classification="NOT_A_TYPE", importance_score=1, confidence=0.5, summary="",
                      reasoning_summary="", potential_impact="", recommended_action="")


def test_configs_load():
    s = load_settings()
    assert s.table("gold_events") == "workspace.market_intel.gold_events"
    src = load_sources()
    names = {c["name"] for c in src["companies"]}
    assert all(x["company"] in names for x in src["sources"])
