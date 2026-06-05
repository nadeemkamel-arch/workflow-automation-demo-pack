from __future__ import annotations

from pathlib import Path

from event_quote_triage import score_row, triage


def test_complete_local_request_scores_high() -> None:
    row = {
        "id": "EVT-X",
        "event_name": "Backyard dinner",
        "event_date": "2026-07-20",
        "event_type": "Dinner",
        "wishlist_items": "dining tables x4, chairs x40",
        "guest_count": "40",
        "city": "San Diego",
        "venue_address": "123 Fictional St",
        "delivery_window": "09:00-11:00",
        "setup_notes": "side gate",
        "budget_notes": "",
    }

    result = score_row(row)

    assert result.readiness == "high"
    assert result.missing_info == "none"
    assert "standard_review" in result.delivery_flags


def test_missing_wishlist_and_date_scores_low() -> None:
    row = {
        "id": "EVT-Y",
        "event_name": "Welcome party",
        "event_date": "TBD",
        "event_type": "",
        "wishlist_items": "",
        "guest_count": "",
        "city": "Encinitas",
        "venue_address": "",
        "delivery_window": "",
        "setup_notes": "beach-adjacent venue",
        "budget_notes": "",
    }

    result = score_row(row)

    assert result.readiness == "low"
    assert "wishlist items and quantities" in result.missing_info
    assert "needs_exact_location" in result.delivery_flags
    assert "Which rental items" in result.draft_follow_up_questions


def test_demo_queue_has_mixed_readiness() -> None:
    demo_dir = Path(__file__).parent
    results = triage(demo_dir / "input" / "event_requests.csv")
    readiness = {item.readiness for item in results}

    assert len(results) == 4
    assert "high" in readiness
    assert "medium" in readiness
    assert "low" in readiness
