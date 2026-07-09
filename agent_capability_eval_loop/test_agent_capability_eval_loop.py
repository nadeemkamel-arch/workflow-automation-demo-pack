from agent_capability_eval_loop import review_runs, summarize


def contract():
    return {
        "global": {
            "min_pass_rate": 0.8,
            "max_tool_error_rate": 0.15,
            "min_trace_coverage": 0.95,
            "min_citation_coverage": 0.9,
            "max_negative_feedback_rate": 0.25,
        },
        "capabilities": {
            "cap": {
                "min_pass_rate": 0.8,
                "must_have_trace_fields": [
                    "scenario_id",
                    "retrieval_set",
                    "decision_reason",
                    "tool_status",
                ],
            }
        },
    }


def row(**overrides):
    base = {
        "scenario_id": "S-1",
        "capability": "cap",
        "scenario": "test",
        "expected_outcome": "right",
        "actual_outcome": "right",
        "passed": True,
        "confidence": 0.9,
        "tool_status": "ok",
        "citation_coverage": 1.0,
        "trace_fields": "scenario_id|retrieval_set|decision_reason|tool_status",
        "trace_field_set": {"scenario_id", "retrieval_set", "decision_reason", "tool_status"},
        "handoff_triggered": False,
        "user_feedback": "positive",
        "latency_ms": 100,
    }
    base.update(overrides)
    if "trace_fields" in overrides and "trace_field_set" not in overrides:
        base["trace_field_set"] = set(filter(None, overrides["trace_fields"].split("|")))
    return base


def test_missing_trace_field_blocks_pilot():
    findings = review_runs([row(trace_fields="scenario_id|decision_reason")], contract())
    summary = summarize([row(trace_fields="scenario_id|decision_reason")], findings, contract())

    assert any(finding.area == "audit_trace" and finding.severity == "blocker" for finding in findings)
    assert summary["decision"] == "block_pilot"


def test_tool_error_and_low_citations_create_high_findings():
    findings = review_runs([row(tool_status="error", citation_coverage=0.4)], contract())

    areas = {finding.area for finding in findings if finding.severity == "high"}
    assert "tool_reliability" in areas
    assert "retrieval_evidence" in areas


def test_low_confidence_without_handoff_is_flagged():
    findings = review_runs([row(confidence=0.52, handoff_triggered=False)], contract())

    assert any(finding.area == "handoff_policy" and finding.severity == "medium" for finding in findings)


def test_capability_rollup_flags_low_pass_rate():
    runs = [
        row(scenario_id="S-1", passed=False, actual_outcome="wrong", user_feedback="negative"),
        row(scenario_id="S-2", passed=False, actual_outcome="wrong", user_feedback="negative"),
        row(scenario_id="S-3", passed=True),
    ]
    findings = review_runs(runs, contract())

    assert any(finding.area == "capability_health" and finding.severity == "high" for finding in findings)


def test_clean_runs_are_ready_for_limited_pilot():
    runs = [row(scenario_id="S-1"), row(scenario_id="S-2")]
    findings = review_runs(runs, contract())
    summary = summarize(runs, findings, contract())

    assert findings == []
    assert summary["decision"] == "ready_for_limited_pilot"
