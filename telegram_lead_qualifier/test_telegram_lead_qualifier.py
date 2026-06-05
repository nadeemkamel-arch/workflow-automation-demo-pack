from __future__ import annotations

from pathlib import Path

from telegram_lead_qualifier import (
    build_ai_summary_payloads,
    build_telegram_notifications,
    process_leads,
)


INPUT = Path(__file__).parent / "input" / "lead_intake.csv"


def test_hot_cash_or_preapproved_leads_route_to_owner_alert() -> None:
    records = process_leads(INPUT)
    by_id = {record.lead_id: record for record in records}

    assert by_id["TL-1001"].priority == "hot"
    assert by_id["TL-1001"].review_route == "telegram_owner_alert"
    assert by_id["TL-1004"].priority == "hot"
    assert by_id["TL-1004"].review_route == "telegram_owner_alert"


def test_non_consenting_lead_routes_to_review() -> None:
    records = process_leads(INPUT)
    lead = next(record for record in records if record.lead_id == "TL-1003")

    assert lead.review_route == "consent_review_queue"
    assert lead.priority == "review"
    assert lead.lead_score < 55


def test_notifications_are_dry_run_and_idempotent() -> None:
    records = process_leads(INPUT)
    notifications = build_telegram_notifications(records)

    assert len(notifications) == 2
    assert all(item["headers"]["X-Dry-Run"] == "true" for item in notifications)
    assert all(item["headers"]["Idempotency-Key"].startswith("telegram-lead:") for item in notifications)
    assert all(item["status"] == "dry_run_only" for item in notifications)


def test_ai_summary_payloads_cover_every_lead_with_schema() -> None:
    records = process_leads(INPUT)
    payloads = build_ai_summary_payloads(records)

    assert len(payloads) == len(records)
    assert {payload["body"]["schema"]["priority"] for payload in payloads} == {"hot|warm|review"}
    assert all(payload["endpoint"] == "/llm/lead-summary" for payload in payloads)
