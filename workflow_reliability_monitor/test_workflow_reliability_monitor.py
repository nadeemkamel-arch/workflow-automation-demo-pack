from __future__ import annotations

from pathlib import Path

from workflow_reliability_monitor import analyze_runs, build_retry_payloads


INPUT = Path(__file__).parent / "input" / "flow_runs.csv"


def test_retryable_failure_routes_to_retry_queue() -> None:
    records = analyze_runs(INPUT)
    run = next(record for record in records if record.run_id == "RUN-1003")

    assert run.severity == "warning"
    assert run.route == "retry_queue"
    assert run.action == "schedule_retry_with_backoff"


def test_exhausted_or_non_retryable_failure_routes_to_incident() -> None:
    records = analyze_runs(INPUT)
    run = next(record for record in records if record.run_id == "RUN-1004")

    assert run.severity == "critical"
    assert run.route == "incident_review"
    assert run.action == "page_owner_and_pause_workflow"


def test_duplicate_idempotency_keys_are_flagged_for_review() -> None:
    records = analyze_runs(INPUT)
    invoice_runs = [record for record in records if record.idempotency_key == "invoice:INV-7781"]

    assert len(invoice_runs) == 2
    assert {record.route for record in invoice_runs} == {"idempotency_review"}


def test_slow_success_routes_to_performance_review() -> None:
    records = analyze_runs(INPUT, slow_threshold=120)
    run = next(record for record in records if record.run_id == "RUN-1005")

    assert run.severity == "notice"
    assert run.route == "performance_review"


def test_retry_payloads_are_dry_run_and_idempotent() -> None:
    records = analyze_runs(INPUT)
    payloads = build_retry_payloads(records)

    assert len(payloads) == 2
    assert all(payload["headers"]["X-Dry-Run"] == "true" for payload in payloads)
    assert all(payload["headers"]["Idempotency-Key"].startswith("retry:") for payload in payloads)
    assert {payload["body"]["workflow"] for payload in payloads} == {"telegram_lead_alert", "crm_sync"}
