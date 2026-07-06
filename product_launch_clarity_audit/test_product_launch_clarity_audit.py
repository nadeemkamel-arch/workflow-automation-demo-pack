from pathlib import Path

from product_launch_clarity_audit import build_issues, launch_decision, load_product, readiness_score, run


FIXTURE = Path(__file__).parent / "input" / "fictional_travel_app.json"


def test_high_risk_trust_and_message_gaps_surface_first():
    product = load_product(FIXTURE)
    issues = build_issues(product)

    top_risks = {issue.risk_type for issue in issues[:4]}
    assert "Trust gap" in top_risks
    assert "Message gap" in top_risks or "Proof gap" in top_risks


def test_readiness_decision_blocks_broad_launch():
    product = load_product(FIXTURE)
    issues = build_issues(product)
    score = readiness_score(product, issues)

    assert score < 75
    assert "broad launch" in launch_decision(score, issues)


def test_run_writes_expected_outputs(tmp_path):
    summary = run(FIXTURE, tmp_path)

    assert summary["issues_found"] == 9
    assert summary["auto_changes_made"] == 0
    assert summary["launch_gate"] == "owner_review_required_before_public_launch"
    assert (tmp_path / "issue_queue.csv").exists()
    assert (tmp_path / "quick_wins.md").read_text(encoding="utf-8").count("Effort:") == 3
    assert "owner_review_required" in (tmp_path / "run_summary.json").read_text(encoding="utf-8")


def test_report_names_scope_boundary(tmp_path):
    run(FIXTURE, tmp_path)
    report = (tmp_path / "readiness_report.md").read_text(encoding="utf-8")

    assert "does not claim production UX research" in report
    assert "ten-person beta" in report
