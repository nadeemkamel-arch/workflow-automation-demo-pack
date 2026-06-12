from __future__ import annotations

from pathlib import Path

from travel_ops_email_hub import (
    build_auto_replies,
    build_booking_payloads,
    build_sheet_rows,
    build_slack_alerts,
    classify_messages,
)


INPUT = Path(__file__).parent / "input" / "travel_messages.csv"


def test_demo_classifies_all_travel_messages() -> None:
    records = classify_messages(INPUT)
    categories = {record.category for record in records}

    assert len(records) == 8
    assert "urgent_traveler_issue" in categories
    assert "hotel_update" in categories
    assert "new_group_request" in categories
    assert "invoice_or_payment" in categories


def test_urgent_messages_create_dry_run_slack_alerts() -> None:
    records = classify_messages(INPUT)
    alerts = build_slack_alerts(records)

    assert len(alerts) == 2
    assert all(alert["status"] == "dry_run_only" for alert in alerts)
    assert alerts[0]["channel"] == "#travel-ops-urgent"
    assert "Idempotency-Key" not in alerts[0]


def test_sheet_rows_are_idempotent_dry_run_writes() -> None:
    records = classify_messages(INPUT)
    sheet_rows = build_sheet_rows(records)

    assert len(sheet_rows) == len(records)
    assert all(row["status"] == "dry_run_only" for row in sheet_rows)
    assert sheet_rows[0]["operation"] == "append_or_update"
    assert sheet_rows[0]["lookupKey"].startswith("travel-email:")


def test_first_contact_auto_reply_is_draft_only_with_loop_protection() -> None:
    records = classify_messages(INPUT)
    replies = build_auto_replies(records)

    assert len(replies) == 1
    assert replies[0]["provider"] == "gmail_draft"
    assert replies[0]["requiresHumanApproval"] is True
    assert replies[0]["status"] == "draft_only"
    assert replies[0]["loopProtectionKey"].startswith("auto-reply:")


def test_booking_payloads_are_staged_with_idempotency_headers() -> None:
    records = classify_messages(INPUT)
    payloads = build_booking_payloads(records)

    assert len(payloads) == 5
    assert all(payload["status"] == "dry_run_only" for payload in payloads)
    assert all(payload["headers"]["X-Dry-Run"] == "true" for payload in payloads)
    assert all(payload["headers"]["Idempotency-Key"].startswith("booking-event:") for payload in payloads)
