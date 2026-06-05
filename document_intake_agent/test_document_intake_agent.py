from __future__ import annotations

from pathlib import Path

from document_intake_agent import parse_document, process_documents


def test_invoice_routes_to_accounts_payable_queue() -> None:
    record, trace, payload = parse_document(Path(__file__).parent / "input" / "documents" / "INV-7781.txt")

    assert record.document_type == "invoice"
    assert record.review_route == "accounts_payable_queue"
    assert record.api_endpoint == "/api/ap/invoices"
    assert payload["headers"]["Idempotency-Key"] == "invoice:INV-7781"
    assert trace.steps[-1]["result"] == "accounts_payable_queue"


def test_contract_with_outbound_campaign_routes_to_compliance() -> None:
    record, _, payload = parse_document(Path(__file__).parent / "input" / "documents" / "CON-208.txt")

    assert record.document_type == "contract"
    assert "outbound_compliance" in record.risk_flags
    assert "manager_approval_amount" in record.risk_flags
    assert record.review_route == "legal_or_compliance_review"
    assert payload["endpoint"] == "/api/reviews/compliance"


def test_purchase_order_deposit_routes_to_manager_review() -> None:
    record, _, payload = parse_document(Path(__file__).parent / "input" / "documents" / "PO-1042.txt")

    assert record.document_type == "purchase_order"
    assert "deposit_required" in record.risk_flags
    assert record.review_route == "manager_review"
    assert payload["body"]["status"] == "ready_for_review"


def test_demo_documents_cover_api_and_review_paths() -> None:
    records, traces, payloads = process_documents(Path(__file__).parent / "input" / "documents")
    routes = {record.review_route for record in records}
    endpoints = {payload["endpoint"] for payload in payloads}

    assert len(records) == 3
    assert len(traces) == 3
    assert {"accounts_payable_queue", "manager_review", "legal_or_compliance_review"} <= routes
    assert "/api/ap/invoices" in endpoints
    assert "/api/reviews/manager" in endpoints
    assert "/api/reviews/compliance" in endpoints
