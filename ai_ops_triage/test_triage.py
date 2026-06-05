from __future__ import annotations

from datetime import date
from pathlib import Path

from triage import score_row, triage


def test_high_value_existing_automation_rescue_scores_high() -> None:
    row = {
        "id": "REQ-X",
        "company": "Cedar Ops",
        "channel": "referral",
        "request": "Our Zapier automation breaks when a lead has two phone numbers",
        "last_touch_days": "21",
        "value_estimate": "1200",
        "deadline": "2026-06-06",
        "notes": "Existing automation; quick rescue",
    }

    result = score_row(row, today=date(2026, 6, 4))

    assert result.priority == "high"
    assert result.score >= 70
    assert result.risk_label == "green"


def test_academic_cheating_request_is_rejected() -> None:
    row = {
        "id": "REQ-BAD",
        "company": "Campus Tutors",
        "channel": "email",
        "request": "Can you write our homework answers with AI?",
        "last_touch_days": "0",
        "value_estimate": "200",
        "deadline": "2026-06-09",
        "notes": "Reject academic cheating",
    }

    result = score_row(row, today=date(2026, 6, 4))

    assert result.priority == "do_not_pursue"
    assert result.score == 0
    assert result.risk_label.startswith("red")


def test_demo_queue_has_actionable_and_rejected_items() -> None:
    demo_dir = Path(__file__).parent
    results = triage(demo_dir / "input" / "inquiries.csv", today=date(2026, 6, 4))
    priorities = {item.priority for item in results}

    assert "high" in priorities
    assert "do_not_pursue" in priorities
    assert len(results) == 6
