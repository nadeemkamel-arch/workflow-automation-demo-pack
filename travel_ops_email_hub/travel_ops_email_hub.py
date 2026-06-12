from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_COLUMNS = {
    "message_id",
    "received_at",
    "sender",
    "subject",
    "body",
    "booking_ref",
    "traveler_name",
    "status_hint",
}

URGENT_TERMS = {
    "urgent",
    "asap",
    "stranded",
    "canceled",
    "cancelled",
    "tonight",
    "tomorrow morning",
    "visa",
}

HOTEL_TERMS = {
    "hotel",
    "room",
    "check-in",
    "rate",
    "reservation",
    "confirmation",
    "frontdesk",
}

INVOICE_TERMS = {"invoice", "deposit", "paid", "payment", "due date"}
STATUS_TERMS = {"follow", "update", "status", "final", "itinerary"}
REQUEST_TERMS = {"quote", "options", "budget", "book", "trip", "workshop"}


@dataclass(frozen=True)
class EmailClassification:
    message_id: str
    received_at: str
    sender: str
    traveler_name: str
    booking_ref: str
    category: str
    priority: str
    confidence: float
    owner_route: str
    sheets_status: str
    review_reason: str
    idempotency_key: str


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        return list(reader)


def _text(row: dict[str, str]) -> str:
    return " ".join([row["sender"], row["subject"], row["body"]]).lower()


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _stable_key(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def classify_message(row: dict[str, str]) -> EmailClassification:
    text = _text(row)
    hint = row["status_hint"].strip().lower()
    booking_ref = row["booking_ref"].strip()

    if hint == "urgent" or _contains_any(text, URGENT_TERMS):
        category = "urgent_traveler_issue"
        priority = "urgent"
        confidence = 0.94
        owner_route = "travel_ops_lead"
        sheets_status = "urgent_review"
        review_reason = "Urgent travel risk terms detected; Slack alert is dry-run only."
    elif hint == "invoice" or _contains_any(text, INVOICE_TERMS):
        category = "invoice_or_payment"
        priority = "normal"
        confidence = 0.84
        owner_route = "finance_review"
        sheets_status = "finance_question"
        review_reason = "Payment language should not trigger an automatic financial response."
    elif hint == "hotel_update" or (_contains_any(text, HOTEL_TERMS) and booking_ref):
        category = "hotel_update"
        priority = "normal"
        confidence = 0.88
        owner_route = "supplier_coordination"
        sheets_status = "hotel_update_pending"
        review_reason = "Hotel or room-block update requires operator review before booking-engine write."
    elif hint == "status_follow_up" or (_contains_any(text, STATUS_TERMS) and booking_ref):
        category = "status_follow_up"
        priority = "normal"
        confidence = 0.82
        owner_route = "agent_queue"
        sheets_status = "follow_up_needed"
        review_reason = "Existing booking follow-up should route to the assigned travel agent."
    elif _contains_any(text, REQUEST_TERMS) and not booking_ref:
        category = "new_group_request"
        priority = "normal"
        confidence = 0.79
        owner_route = "new_request_queue"
        sheets_status = "new_lead"
        review_reason = "New request can receive a draft acknowledgement after duplicate check."
    else:
        category = "unknown_review"
        priority = "review"
        confidence = 0.55
        owner_route = "manual_review"
        sheets_status = "needs_triage"
        review_reason = "Message does not match the approved travel operations routes."

    return EmailClassification(
        message_id=row["message_id"],
        received_at=row["received_at"],
        sender=row["sender"],
        traveler_name=row["traveler_name"],
        booking_ref=booking_ref or "unassigned",
        category=category,
        priority=priority,
        confidence=confidence,
        owner_route=owner_route,
        sheets_status=sheets_status,
        review_reason=review_reason,
        idempotency_key=_stable_key("travel-email", row["message_id"], row["subject"], booking_ref),
    )


def classify_messages(path: Path) -> list[EmailClassification]:
    rows = read_rows(path)
    if not rows:
        raise ValueError(f"No travel messages found in {path}")
    return [classify_message(row) for row in rows]


def build_sheet_rows(records: list[EmailClassification]) -> list[dict[str, object]]:
    rows = []
    for record in records:
        rows.append(
            {
                "range": "TravelOps!A:K",
                "operation": "append_or_update",
                "lookupKey": record.idempotency_key,
                "values": {
                    "messageId": record.message_id,
                    "receivedAt": record.received_at,
                    "sender": record.sender,
                    "travelerName": record.traveler_name,
                    "bookingRef": record.booking_ref,
                    "category": record.category,
                    "priority": record.priority,
                    "status": record.sheets_status,
                    "ownerRoute": record.owner_route,
                    "confidence": record.confidence,
                    "reviewReason": record.review_reason,
                },
                "status": "dry_run_only",
            }
        )
    return rows


def build_slack_alerts(records: list[EmailClassification]) -> list[dict[str, object]]:
    alerts = []
    for record in records:
        if record.category != "urgent_traveler_issue":
            continue
        alerts.append(
            {
                "channel": "#travel-ops-urgent",
                "text": (
                    f"Urgent travel issue: {record.traveler_name} "
                    f"({record.booking_ref}) from message {record.message_id}"
                ),
                "blocks": [
                    {"type": "section", "text": f"Route: {record.owner_route}"},
                    {"type": "context", "text": record.review_reason},
                ],
                "idempotencyKey": _stable_key("slack-alert", record.idempotency_key),
                "status": "dry_run_only",
            }
        )
    return alerts


def build_auto_replies(records: list[EmailClassification]) -> list[dict[str, object]]:
    replies = []
    for record in records:
        if record.category != "new_group_request":
            continue
        replies.append(
            {
                "provider": "gmail_draft",
                "to": record.sender,
                "subject": "Re: your group travel request",
                "body": (
                    f"Hi {record.traveler_name},\n\n"
                    "Thanks for the details. We are reviewing the request and will confirm options, "
                    "budget range, and missing details before anything is booked.\n\n"
                    "Best,\nTravel Ops"
                ),
                "loopProtectionKey": _stable_key("auto-reply", record.sender, record.traveler_name),
                "requiresHumanApproval": True,
                "status": "draft_only",
            }
        )
    return replies


def build_booking_payloads(records: list[EmailClassification]) -> list[dict[str, object]]:
    payloads = []
    for record in records:
        if record.booking_ref == "unassigned" or record.category not in {
            "hotel_update",
            "status_follow_up",
            "urgent_traveler_issue",
        }:
            continue
        payloads.append(
            {
                "method": "PATCH",
                "endpoint": f"/bookings/{record.booking_ref}/inbox-events",
                "headers": {
                    "Idempotency-Key": _stable_key("booking-event", record.idempotency_key),
                    "X-Dry-Run": "true",
                },
                "body": {
                    "messageId": record.message_id,
                    "category": record.category,
                    "priority": record.priority,
                    "ownerRoute": record.owner_route,
                    "status": record.sheets_status,
                    "requiresHumanApproval": True,
                },
                "status": "dry_run_only",
            }
        )
    return payloads


def _count_by(records: list[EmailClassification], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(getattr(record, field_name))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def render_ops_digest(records: list[EmailClassification]) -> str:
    lines = [
        "# Travel Ops Email Hub Digest",
        "",
        "Fictional dry-run output. No Gmail, Slack, Sheets, or booking-engine action was taken.",
        "",
        "| Message | Traveler | Booking | Category | Priority | Route | Review |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            f"| {record.message_id} | {record.traveler_name} | {record.booking_ref} | "
            f"{record.category} | {record.priority} | {record.owner_route} | {record.review_reason} |"
        )
    lines.extend(
        [
            "",
            "## Launch Gate",
            "",
            "- Confirm the five email categories and status names before writing to live Sheets.",
            "- Keep Slack alerts dry-run until urgent keywords and on-call ownership are approved.",
            "- Create Gmail drafts only after duplicate and loop-protection checks pass.",
            "- Treat booking-engine writes as staged API payloads until REST docs, auth, and rollback rules are reviewed.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def write_outputs(records: list[EmailClassification], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_records = sorted(records, key=lambda record: record.message_id)

    with (out_dir / "classification_queue.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(asdict(sorted_records[0]).keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(asdict(record) for record in sorted_records)

    (out_dir / "google_sheets_rows.json").write_text(
        json.dumps(build_sheet_rows(sorted_records), indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "slack_alerts.json").write_text(
        json.dumps(build_slack_alerts(sorted_records), indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "draft_auto_replies.json").write_text(
        json.dumps(build_auto_replies(sorted_records), indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "booking_api_payloads.json").write_text(
        json.dumps(build_booking_payloads(sorted_records), indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "ops_digest.md").write_text(render_ops_digest(sorted_records), encoding="utf-8")
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "message_count": len(sorted_records),
                "category_counts": _count_by(sorted_records, "category"),
                "priority_counts": _count_by(sorted_records, "priority"),
                "sheet_row_count": len(build_sheet_rows(sorted_records)),
                "slack_alert_count": len(build_slack_alerts(sorted_records)),
                "draft_auto_reply_count": len(build_auto_replies(sorted_records)),
                "booking_api_payload_count": len(build_booking_payloads(sorted_records)),
                "live_action_count": 0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a dry-run travel ops email automation pack.")
    parser.add_argument("--input", type=Path, required=True, help="CSV file of fictional travel messages.")
    parser.add_argument("--out", type=Path, required=True, help="Directory for generated output files.")
    args = parser.parse_args()

    records = classify_messages(args.input)
    write_outputs(records, args.out)
    print(f"Built {len(records)} dry-run travel ops records at {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
