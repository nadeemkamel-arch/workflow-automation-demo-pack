from __future__ import annotations

from pathlib import Path

from statement_email_workflow import build_send_payload, build_statements


def test_demo_builds_pair_and_external_statements() -> None:
    statements = build_statements(Path(__file__).parent / "input" / "session_records.csv")
    types = {statement.statement_type for statement in statements}

    assert len(statements) == 10
    assert "party_pair_weekly" in types
    assert "external_recipient_weekly" in types


def test_pair_statement_groups_same_parties_for_week() -> None:
    statements = build_statements(Path(__file__).parent / "input" / "session_records.csv")
    target = next(
        statement
        for statement in statements
        if statement.statement_id == "pair:2026-06-01:North-Clinic:River-Billing"
    )

    assert target.session_count == 2
    assert target.total_minutes == 60
    assert target.total_amount_usd == 225.0
    assert "ops+north@example.test" in target.to
    assert "billing+river@example.test" in target.to


def test_external_statement_groups_by_recipient() -> None:
    statements = build_statements(Path(__file__).parent / "input" / "session_records.csv")
    target = next(
        statement
        for statement in statements
        if statement.statement_id == "external:2026-06-01:lee@example.test"
    )

    assert target.session_count == 2
    assert target.total_amount_usd == 225.0
    assert target.to == "lee@example.test"
    assert "S-1001" in target.body_preview
    assert "S-1002" in target.body_preview


def test_send_payload_is_dry_run_with_idempotency_key() -> None:
    statement = build_statements(Path(__file__).parent / "input" / "session_records.csv")[0]
    payload = build_send_payload(statement)

    assert payload["method"] == "POST"
    assert payload["headers"]["X-Dry-Run"] == "true"
    assert payload["headers"]["Idempotency-Key"] == statement.statement_id
    assert payload["body"]["subject"] == statement.subject
