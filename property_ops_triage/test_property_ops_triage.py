from __future__ import annotations

from pathlib import Path

from property_ops_triage import (
    build_asana_payload,
    build_invoice_packets,
    build_triage,
)


INPUT = Path(__file__).parent / "input" / "property_messages.csv"


def test_demo_routes_property_messages() -> None:
    _messages, decisions = build_triage(INPUT)
    categories = {decision.category for decision in decisions}

    assert len(decisions) == 10
    assert "maintenance_request" in categories
    assert "vendor_invoice" in categories
    assert "vendor_statement_export" in categories
    assert "invoice_duplicate_review" in categories
    assert "tenant_admin" in categories


def test_water_leak_routes_to_urgent_maintenance() -> None:
    _messages, decisions = build_triage(INPUT)
    target = next(decision for decision in decisions if decision.message_id == "M-1001")

    assert target.category == "maintenance_request"
    assert target.priority == "urgent"
    assert target.owner_route == "maintenance_dispatch"
    assert target.idempotency_key.startswith("pm-")


def test_duplicate_invoice_blocks_live_posting() -> None:
    _messages, decisions = build_triage(INPUT)
    target = next(decision for decision in decisions if decision.message_id == "M-1008")

    assert target.category == "invoice_duplicate_review"
    assert target.owner_route == "accounting_review"
    assert "duplicate invoice" in target.review_reason.lower()


def test_invoice_packets_include_quickbooks_dry_run_payloads() -> None:
    messages, decisions = build_triage(INPUT)
    packets = build_invoice_packets(messages, decisions)

    assert len(packets) == 4
    assert all(packet["status"] == "review_required" for packet in packets)
    assert all(packet["quickbooks_draft_payload"]["mode"] == "dry_run" for packet in packets)


def test_asana_payload_keeps_external_action_in_dry_run() -> None:
    _messages, decisions = build_triage(INPUT)
    payload = build_asana_payload(decisions[0])

    assert payload["provider"] == "asana"
    assert payload["mode"] == "dry_run"
    assert payload["idempotency_key"] == decisions[0].idempotency_key
