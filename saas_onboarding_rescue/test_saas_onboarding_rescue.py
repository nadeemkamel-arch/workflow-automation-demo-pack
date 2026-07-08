from pathlib import Path

from saas_onboarding_rescue import build_queue, load_users, run


BASE = Path(__file__).parent


def test_queue_prioritizes_blocked_and_high_intent_users():
    users = load_users(BASE / "input" / "trial_users.csv")
    rules = {"quiet_hours": 24, "stale_hours": 72, "sprint_days": 7}

    queue = build_queue(users, rules)
    by_company = {item.user.company: item for item in queue}

    assert by_company["FounderDesk"].email_key == "demo_invite"
    assert by_company["SketchLedger"].email_key == "human_unblocker"
    assert by_company["Northstar Ops"].email_key == "setup_nudge"
    assert by_company["QuietBeta"].email_key == "last_chance_checkin"


def test_do_not_contact_records_are_suppressed():
    users = load_users(BASE / "input" / "trial_users.csv")
    rules = {"quiet_hours": 24, "stale_hours": 72, "sprint_days": 7}

    queue = build_queue(users, rules)
    opt_out = next(item for item in queue if item.user.company == "OptOut Labs")

    assert opt_out.suppressed is True
    assert opt_out.email_key == "suppress"
    assert opt_out.risk_score == 0


def test_run_writes_expected_outputs(tmp_path):
    out_dir = tmp_path / "out"
    queue = run(
        BASE / "input" / "trial_users.csv",
        BASE / "input" / "email_rules.json",
        out_dir,
    )

    assert len(queue) == 5
    assert (out_dir / "activation_queue.csv").exists()
    assert (out_dir / "dry_run_payloads.json").read_text(encoding="utf-8").count('"dry_run": true') == 4
    assert "founder reviews copy" in (out_dir / "email_sequence.md").read_text(encoding="utf-8").lower()
    assert '"live_actions": 0' in (out_dir / "run_summary.json").read_text(encoding="utf-8")


if __name__ == "__main__":
    import tempfile

    test_queue_prioritizes_blocked_and_high_intent_users()
    test_do_not_contact_records_are_suppressed()
    with tempfile.TemporaryDirectory() as tmp:
        test_run_writes_expected_outputs(Path(tmp))
    print("3 tests passed")
