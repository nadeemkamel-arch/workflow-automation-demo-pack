from pathlib import Path

from whatsapp_handoff_state_machine import load_messages, load_rules, run, decide_message


ROOT = Path(__file__).parent


def test_normal_quote_goes_to_approval_queue():
    rules = load_rules(ROOT / "input/business_rules.json")
    message = load_messages(ROOT / "input/messages.csv")[0]

    decision = decide_message(message, rules)

    assert decision.route == "draft_for_approval"
    assert decision.mode_after == "ai"
    assert "quantity" in decision.draft_reply.lower()
    assert decision.approval_url.endswith("/c-101")


def test_risky_request_goes_to_human_handoff():
    rules = load_rules(ROOT / "input/business_rules.json")
    message = load_messages(ROOT / "input/messages.csv")[1]

    decision = decide_message(message, rules)

    assert decision.route == "human_handoff"
    assert decision.mode_after == "human"
    assert decision.urgency == "high"
    assert "not working" in decision.reason


def test_human_mode_remains_paused_before_resume_window():
    rules = load_rules(ROOT / "input/business_rules.json")
    message = load_messages(ROOT / "input/messages.csv")[2]

    decision = decide_message(message, rules)

    assert decision.route == "ai_paused"
    assert decision.mode_after == "human"
    assert decision.draft_reply == ""


def test_run_writes_expected_outputs(tmp_path):
    summary = run(
        ROOT / "input/messages.csv",
        ROOT / "input/business_rules.json",
        tmp_path,
    )

    assert summary["messages_processed"] == 5
    assert summary["drafts_waiting_for_approval"] == 2
    assert summary["human_handoffs"] == 2
    assert summary["ai_paused_threads"] == 1
    assert summary["auto_sends"] == 0
    assert (tmp_path / "approval_queue.csv").exists()
    assert (tmp_path / "handoff_packets.md").exists()
    assert (tmp_path / "run_summary.json").exists()
