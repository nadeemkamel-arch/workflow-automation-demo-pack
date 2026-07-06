from pathlib import Path

from prelaunch_qa_smoke_pack import build_findings, coverage_gaps, load_plan, load_sessions, release_decision, run


BASE = Path(__file__).parent
SESSIONS = BASE / "input" / "test_sessions.csv"
PLAN = BASE / "input" / "test_plan.json"


def test_blocker_and_accessibility_findings_surface_early():
    findings = build_findings(load_sessions(SESSIONS))

    assert findings[0].severity == "blocker"
    assert any(finding.category == "accessibility" for finding in findings[:5])


def test_coverage_gap_blocks_wider_beta():
    plan = load_plan(PLAN)
    sessions = load_sessions(SESSIONS)
    gaps = coverage_gaps(plan, sessions)
    decision = release_decision(plan, build_findings(sessions), gaps, [])

    assert "Account deletion" in gaps
    assert "not ready" in decision


def test_run_writes_expected_outputs(tmp_path):
    summary = run(SESSIONS, PLAN, tmp_path)

    assert summary["sessions_reviewed"] == 10
    assert summary["findings_found"] == 8
    assert summary["severity_counts"]["blocker"] >= 1
    assert summary["auto_changes_made"] == 0
    assert summary["launch_gate"] == "owner_review_required_before_beta_invites"
    assert (tmp_path / "bug_report.csv").exists()
    assert "Retest Checklist" in (tmp_path / "retest_checklist.md").read_text(encoding="utf-8")


def test_ux_feedback_names_practical_product_note(tmp_path):
    run(SESSIONS, PLAN, tmp_path)
    feedback = (tmp_path / "ux_feedback.md").read_text(encoding="utf-8")

    assert "Highest Leverage Feedback" in feedback
    assert "first beta invite should wait" in feedback
