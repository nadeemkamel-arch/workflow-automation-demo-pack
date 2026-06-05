from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

DOCUMENT_ID_PATTERNS = {
    "purchase_order": re.compile(r"^Purchase Order:\s*(?P<id>\S+)", re.MULTILINE),
    "invoice": re.compile(r"^Invoice:\s*(?P<id>\S+)", re.MULTILINE),
    "contract": re.compile(r"^Contract:\s*(?P<id>\S+)", re.MULTILINE),
}

FIELD_PATTERNS = {
    "vendor": re.compile(r"^Vendor:\s*(?P<value>.+)", re.MULTILINE),
    "requester": re.compile(r"^Requester:\s*(?P<value>.+)", re.MULTILINE),
    "department": re.compile(r"^Department:\s*(?P<value>.+)", re.MULTILINE),
    "amount": re.compile(r"^Amount:\s*(?P<value>[0-9,.]+)\s*USD", re.MULTILINE),
    "due_date": re.compile(r"^Due Date:\s*(?P<value>\d{4}-\d{2}-\d{2})", re.MULTILINE),
    "notes": re.compile(r"^Notes:\s*(?P<value>.+)", re.MULTILINE),
}

REVIEW_KEYWORDS = {
    "deposit_required": {"deposit", "prepay", "advance payment"},
    "outbound_compliance": {"outbound", "email sequence", "lead research"},
    "rush_timing": {"rush", "urgent", "same day"},
}


@dataclass(frozen=True)
class IntakeRecord:
    document_id: str
    document_type: str
    vendor: str
    requester: str
    department: str
    amount_usd: float
    due_date: str
    risk_flags: str
    review_route: str
    api_endpoint: str
    idempotency_key: str


@dataclass(frozen=True)
class ToolTrace:
    document_id: str
    steps: list[dict[str, str]]


def _match_required(pattern: re.Pattern[str], text: str, field_name: str) -> str:
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Missing required field: {field_name}")
    return match.group("value" if "value" in match.groupdict() else "id").strip()


def classify_document(text: str) -> tuple[str, str]:
    for document_type, pattern in DOCUMENT_ID_PATTERNS.items():
        match = pattern.search(text)
        if match:
            return document_type, match.group("id").strip()
    raise ValueError("Could not classify document type")


def detect_risks(text: str, amount: float) -> list[str]:
    normalized = text.lower()
    flags = [
        flag
        for flag, keywords in REVIEW_KEYWORDS.items()
        if any(keyword in normalized for keyword in keywords)
    ]
    if amount >= 2500:
        flags.append("manager_approval_amount")
    return flags or ["standard"]


def choose_route(document_type: str, risk_flags: list[str]) -> str:
    if "outbound_compliance" in risk_flags:
        return "legal_or_compliance_review"
    if "manager_approval_amount" in risk_flags or "deposit_required" in risk_flags:
        return "manager_review"
    if document_type == "invoice":
        return "accounts_payable_queue"
    return "ops_review_queue"


def build_api_endpoint(document_type: str, route: str) -> str:
    if route == "accounts_payable_queue":
        return "/api/ap/invoices"
    if route == "legal_or_compliance_review":
        return "/api/reviews/compliance"
    if route == "manager_review":
        return "/api/reviews/manager"
    if document_type == "purchase_order":
        return "/api/procurement/purchase-orders"
    return "/api/ops/intake"


def parse_document(path: Path) -> tuple[IntakeRecord, ToolTrace, dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    document_type, document_id = classify_document(text)
    amount = float(_match_required(FIELD_PATTERNS["amount"], text, "amount").replace(",", ""))
    risk_flags = detect_risks(text, amount)
    route = choose_route(document_type, risk_flags)
    endpoint = build_api_endpoint(document_type, route)
    vendor = _match_required(FIELD_PATTERNS["vendor"], text, "vendor")
    requester = _match_required(FIELD_PATTERNS["requester"], text, "requester")
    department = _match_required(FIELD_PATTERNS["department"], text, "department")
    due_date = _match_required(FIELD_PATTERNS["due_date"], text, "due_date")
    notes = _match_required(FIELD_PATTERNS["notes"], text, "notes")

    record = IntakeRecord(
        document_id=document_id,
        document_type=document_type,
        vendor=vendor,
        requester=requester,
        department=department,
        amount_usd=amount,
        due_date=due_date,
        risk_flags=", ".join(risk_flags),
        review_route=route,
        api_endpoint=endpoint,
        idempotency_key=f"{document_type}:{document_id}",
    )
    payload = {
        "method": "POST",
        "endpoint": endpoint,
        "headers": {
            "Idempotency-Key": record.idempotency_key,
            "X-Review-Route": route,
        },
        "body": {
            "documentId": document_id,
            "documentType": document_type,
            "vendor": vendor,
            "requester": requester,
            "department": department,
            "amountUsd": amount,
            "dueDate": due_date,
            "riskFlags": risk_flags,
            "notes": notes,
            "status": "ready_for_review" if route.endswith("review") or "review" in route else "ready_to_queue",
        },
    }
    trace = ToolTrace(
        document_id=document_id,
        steps=[
            {"tool": "read_document", "result": path.name},
            {"tool": "classify_document", "result": document_type},
            {"tool": "extract_fields", "result": "vendor, requester, department, amount, due date, notes"},
            {"tool": "validate_amount_and_date", "result": "passed"},
            {"tool": "detect_risk_flags", "result": record.risk_flags},
            {"tool": "build_api_payload", "result": f"POST {endpoint}"},
            {"tool": "route_for_review", "result": route},
        ],
    )
    return record, trace, payload


def process_documents(input_dir: Path) -> tuple[list[IntakeRecord], list[ToolTrace], list[dict[str, object]]]:
    paths = sorted(input_dir.glob("*.txt"))
    if not paths:
        raise ValueError(f"No .txt documents found in {input_dir}")
    records: list[IntakeRecord] = []
    traces: list[ToolTrace] = []
    payloads: list[dict[str, object]] = []
    for path in paths:
        record, trace, payload = parse_document(path)
        records.append(record)
        traces.append(trace)
        payloads.append(payload)
    return records, traces, payloads


def _count_by(records: list[IntakeRecord], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(getattr(record, field_name))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def render_review_queue(records: list[IntakeRecord]) -> str:
    lines = [
        "# Document Intake Review Queue",
        "",
        "Fictional sample output. API payloads are staged for review, not sent.",
        "",
        "| Document | Type | Vendor | Amount | Risk Flags | Route | API Endpoint |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            f"| {record.document_id} | {record.document_type} | {record.vendor} | "
            f"{record.amount_usd:.2f} | {record.risk_flags} | {record.review_route} | "
            f"{record.api_endpoint} |"
        )
    lines.extend(
        [
            "",
            "## Launch Gate",
            "",
            "- Replace sample documents with approved exports or sandbox files.",
            "- Confirm destination API endpoints, auth scope, and idempotency behavior.",
            "- Keep payment, compliance, and outbound-campaign items in human review.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def write_outputs(
    records: list[IntakeRecord],
    traces: list[ToolTrace],
    payloads: list[dict[str, object]],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_records = sorted(records, key=lambda item: item.document_id)

    (out_dir / "review_queue.md").write_text(render_review_queue(sorted_records), encoding="utf-8")
    (out_dir / "api_payloads.json").write_text(json.dumps(payloads, indent=2), encoding="utf-8")
    (out_dir / "agent_trace.json").write_text(
        json.dumps([asdict(trace) for trace in traces], indent=2),
        encoding="utf-8",
    )
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "total": len(sorted_records),
                "by_document_type": _count_by(sorted_records, "document_type"),
                "by_review_route": _count_by(sorted_records, "review_route"),
                "human_review_ids": [
                    record.document_id
                    for record in sorted_records
                    if "review" in record.review_route
                ],
                "api_endpoints": sorted({record.api_endpoint for record in sorted_records}),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse fictional business documents into reviewed API handoff payloads."
    )
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory of fictional .txt documents.")
    parser.add_argument("--out", type=Path, required=True, help="Directory for generated output files.")
    args = parser.parse_args()

    records, traces, payloads = process_documents(args.input_dir)
    write_outputs(records, traces, payloads, args.out)
    print(f"Processed {len(records)} documents into staged API payloads at {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
