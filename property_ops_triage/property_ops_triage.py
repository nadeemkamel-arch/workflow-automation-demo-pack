from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_COLUMNS = {
    "message_id",
    "thread_id",
    "received_at",
    "sender_name",
    "sender_email",
    "property",
    "unit",
    "subject",
    "body",
    "attachment_names",
    "amount_usd",
}

VENDOR_HINTS = {"invoice", "billing", "statement", "vendor", "quickbooks", "past due", "service date"}
MAINTENANCE_HINTS = {"leak", "water", "repair", "ac", "cooling", "maintenance", "emergency", "fob"}
TENANT_HINTS = {"noise", "complaint", "lease", "renewal", "parking", "package room", "access"}
URGENT_HINTS = {"emergency", "water", "leak", "not cooling", "83 degrees", "refrigerated", "past due"}


@dataclass(frozen=True)
class PropertyMessage:
    message_id: str
    thread_id: str
    received_at: str
    sender_name: str
    sender_email: str
    property: str
    unit: str
    subject: str
    body: str
    attachment_names: str
    amount_usd: float


@dataclass(frozen=True)
class TriageDecision:
    message_id: str
    thread_id: str
    property: str
    unit: str
    sender_email: str
    category: str
    priority: str
    owner_route: str
    confidence: float
    review_reason: str
    idempotency_key: str
    dry_run_action: str


def read_messages(path: Path) -> list[PropertyMessage]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        return [
            PropertyMessage(
                message_id=row["message_id"],
                thread_id=row["thread_id"],
                received_at=row["received_at"],
                sender_name=row["sender_name"],
                sender_email=row["sender_email"],
                property=row["property"],
                unit=row["unit"],
                subject=row["subject"],
                body=row["body"],
                attachment_names=row["attachment_names"],
                amount_usd=float(row["amount_usd"] or 0),
            )
            for row in reader
        ]


def _contains_any(text: str, hints: set[str]) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in hints)


def _attachment_hash(message: PropertyMessage) -> str:
    normalized = "|".join(
        part.strip().lower()
        for part in message.attachment_names.split(";")
        if part.strip()
    )
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10] if normalized else "no-attachment"


def build_idempotency_key(message: PropertyMessage) -> str:
    raw = f"{message.thread_id}:{message.message_id}:{_attachment_hash(message)}"
    return "pm-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def classify_message(message: PropertyMessage) -> TriageDecision:
    text = f"{message.sender_email} {message.subject} {message.body} {message.attachment_names}"
    has_invoice_attachment = ".pdf" in message.attachment_names.lower() and _contains_any(text, VENDOR_HINTS)
    is_statement_export = "statement" in text.lower() and "export" in text.lower() and message.amount_usd == 0
    is_vendor = has_invoice_attachment or _contains_any(message.sender_email, {"billing", "ap@", "quickbooks", "portal"})
    is_maintenance = _contains_any(text, MAINTENANCE_HINTS)
    is_tenant = _contains_any(text, TENANT_HINTS) or bool(message.unit)
    is_urgent = _contains_any(text, URGENT_HINTS)

    if "duplicate" in text.lower():
        category = "invoice_duplicate_review"
        owner_route = "accounting_review"
        priority = "high"
        confidence = 0.92
        review_reason = "Possible duplicate invoice signal; block live posting until accounting confirms."
        dry_run_action = "Create accounting review item only."
    elif is_statement_export:
        category = "vendor_statement_export"
        owner_route = "accounting_review"
        priority = "normal"
        confidence = 0.82
        review_reason = "Vendor statement/export detected; review before reconciliation, but do not create invoice draft."
        dry_run_action = "Create accounting review item without QuickBooks invoice draft."
    elif is_vendor:
        category = "vendor_invoice"
        owner_route = "accounting_review"
        priority = "high" if message.amount_usd >= 1000 or "past due" in text.lower() else "normal"
        confidence = 0.88 if has_invoice_attachment else 0.74
        review_reason = "Invoice-like message; extract fields and route to reviewer before QuickBooks draft."
        dry_run_action = "Build invoice packet and staged QuickBooks draft payload."
    elif is_maintenance:
        category = "maintenance_request"
        owner_route = "maintenance_dispatch"
        priority = "urgent" if is_urgent else "normal"
        confidence = 0.86 if message.unit else 0.72
        review_reason = "Maintenance wording detected; dispatch draft stays behind human approval."
        dry_run_action = "Create Asana maintenance task draft and Slack digest line."
    elif is_tenant:
        category = "tenant_admin"
        owner_route = "property_manager_review"
        priority = "normal"
        confidence = 0.78
        review_reason = "Tenant/admin issue; manager review before any tenant response."
        dry_run_action = "Create property manager review item."
    else:
        category = "needs_human_review"
        owner_route = "ops_review"
        priority = "normal"
        confidence = 0.55
        review_reason = "No deterministic route matched with enough confidence."
        dry_run_action = "Place in manual review queue."

    return TriageDecision(
        message_id=message.message_id,
        thread_id=message.thread_id,
        property=message.property,
        unit=message.unit or "not_applicable",
        sender_email=message.sender_email,
        category=category,
        priority=priority,
        owner_route=owner_route,
        confidence=confidence,
        review_reason=review_reason,
        idempotency_key=build_idempotency_key(message),
        dry_run_action=dry_run_action,
    )


def build_triage(input_path: Path) -> tuple[list[PropertyMessage], list[TriageDecision]]:
    messages = read_messages(input_path)
    return messages, [classify_message(message) for message in messages]


def build_asana_payload(decision: TriageDecision) -> dict[str, object]:
    return {
        "provider": "asana",
        "mode": "dry_run",
        "idempotency_key": decision.idempotency_key,
        "task": {
            "name": f"{decision.property}: {decision.category} ({decision.priority})",
            "project": decision.owner_route,
            "custom_fields": {
                "message_id": decision.message_id,
                "thread_id": decision.thread_id,
                "property": decision.property,
                "unit": decision.unit,
                "confidence": decision.confidence,
            },
            "notes": decision.review_reason,
        },
    }


def build_slack_digest(decisions: list[TriageDecision]) -> str:
    lines = [
        "# Property Ops Triage Digest",
        "",
        "Fictional dry-run output. No tenant, vendor, Slack, Asana, or QuickBooks action was taken.",
        "",
        "| Priority | Property | Unit | Category | Route | Confidence |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    priority_order = {"urgent": 0, "high": 1, "normal": 2}
    for decision in sorted(decisions, key=lambda item: (priority_order[item.priority], item.property, item.message_id)):
        lines.append(
            f"| {decision.priority} | {decision.property} | {decision.unit} | "
            f"{decision.category} | {decision.owner_route} | {decision.confidence:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Launch Gates",
            "",
            "- Confirm categories against 20-50 real redacted messages before enabling live labels.",
            "- Keep tenant/vendor replies in draft mode until manager approval.",
            "- Require idempotency keys before creating Asana tasks or QuickBooks drafts.",
            "- Route duplicate invoice warnings to accounting review only.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def build_invoice_packets(messages: list[PropertyMessage], decisions: list[TriageDecision]) -> list[dict[str, object]]:
    by_id = {message.message_id: message for message in messages}
    packets: list[dict[str, object]] = []
    for decision in decisions:
        if decision.category not in {"vendor_invoice", "invoice_duplicate_review"}:
            continue
        message = by_id[decision.message_id]
        packets.append(
            {
                "message_id": message.message_id,
                "property": message.property,
                "vendor_email": message.sender_email,
                "attachment_names": [part.strip() for part in message.attachment_names.split(";") if part.strip()],
                "amount_usd": message.amount_usd,
                "review_route": decision.owner_route,
                "status": "review_required",
                "quickbooks_draft_payload": {
                    "mode": "dry_run",
                    "idempotency_key": decision.idempotency_key,
                    "vendor": message.sender_name,
                    "property": message.property,
                    "amount_usd": message.amount_usd,
                    "source_message_id": message.message_id,
                    "memo": f"Review before posting: {message.subject}",
                },
                "blocker": decision.review_reason,
            }
        )
    return packets


def write_outputs(messages: list[PropertyMessage], decisions: list[TriageDecision], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "triage_queue.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(asdict(decisions[0]).keys()) if decisions else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for decision in decisions:
            writer.writerow(asdict(decision))

    asana_payloads = [build_asana_payload(decision) for decision in decisions]
    invoice_packets = build_invoice_packets(messages, decisions)
    route_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    for decision in decisions:
        route_counts[decision.owner_route] = route_counts.get(decision.owner_route, 0) + 1
        priority_counts[decision.priority] = priority_counts.get(decision.priority, 0) + 1

    (out_dir / "asana_task_payloads.json").write_text(json.dumps(asana_payloads, indent=2), encoding="utf-8")
    (out_dir / "invoice_review_packets.json").write_text(json.dumps(invoice_packets, indent=2), encoding="utf-8")
    (out_dir / "slack_owner_digest.md").write_text(build_slack_digest(decisions), encoding="utf-8")
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "message_count": len(messages),
                "route_counts": dict(sorted(route_counts.items())),
                "priority_counts": dict(sorted(priority_counts.items())),
                "invoice_packets": len(invoice_packets),
                "send_mode": "dry_run_only",
                "live_actions_taken": 0,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a dry-run property-management ops triage packet.")
    parser.add_argument("--input", type=Path, required=True, help="CSV file of fictional property inbox messages.")
    parser.add_argument("--out", type=Path, required=True, help="Directory for generated output files.")
    args = parser.parse_args()

    messages, decisions = build_triage(args.input)
    write_outputs(messages, decisions, args.out)
    print(f"Built {len(decisions)} property ops triage decisions at {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
