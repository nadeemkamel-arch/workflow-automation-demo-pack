from __future__ import annotations

from pathlib import Path

from finance_context_layer import build_packets, write_outputs


ROOT = Path(__file__).parent
RECORDS = ROOT / "input" / "source_records.csv"
REQUESTS = ROOT / "input" / "operator_requests.csv"


def test_invoice_question_retrieves_invoice_and_slack_context() -> None:
    packets = build_packets(RECORDS, REQUESTS)
    packet = next(item for item in packets if item.request_id == "REQ-2001")
    source_ids = {source["source_id"] for source in packet.cited_sources}

    assert {"SRC-1001", "SRC-1003"}.issubset(source_ids)
    assert packet.route == "ready_for_analyst_review"
    assert packet.live_action_allowed is False


def test_cross_client_records_do_not_leak_into_packet() -> None:
    packets = build_packets(RECORDS, REQUESTS)
    packet = next(item for item in packets if item.request_id == "REQ-2004")
    source_ids = {source["source_id"] for source in packet.cited_sources}

    assert "SRC-1004" not in source_ids
    assert packet.route == "needs_more_context"
    assert packet.missing_source_types == ["invoice"]


def test_payment_request_is_restricted_even_with_context() -> None:
    packets = build_packets(RECORDS, REQUESTS)
    packet = next(item for item in packets if item.request_id == "REQ-2002")

    assert packet.route == "restricted_action_review"
    assert packet.next_action == "review_sources_before_payment_decision"
    assert packet.dry_run_payload["status"] == "dry_run_only"
    assert packet.live_action_allowed is False


def test_sensitive_payroll_context_requires_owner_review() -> None:
    packets = build_packets(RECORDS, REQUESTS)
    packet = next(item for item in packets if item.request_id == "REQ-2003")

    assert packet.route == "sensitive_context_review"
    assert packet.next_action == "finance_owner_review_required"
    assert "SRC-1005" in {source["source_id"] for source in packet.cited_sources}


def test_write_outputs_creates_handoff_files(tmp_path: Path) -> None:
    packets = build_packets(RECORDS, REQUESTS)
    write_outputs(packets, tmp_path)

    assert (tmp_path / "context_packets.json").exists()
    assert (tmp_path / "action_queue.csv").exists()
    assert (tmp_path / "finance_ops_digest.md").exists()
    assert (tmp_path / "run_summary.json").exists()
