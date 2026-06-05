from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_COLUMNS = {
    "lead_id",
    "source_ref",
    "language",
    "contact_name",
    "contact_handle",
    "budget_usd",
    "city",
    "property_type",
    "timeline",
    "financing_status",
    "notes",
    "consent_to_contact",
}


@dataclass(frozen=True)
class LeadRecord:
    lead_id: str
    source_ref: str
    language: str
    contact_name: str
    contact_handle: str
    budget_usd: int
    city: str
    property_type: str
    timeline: str
    financing_status: str
    lead_score: int
    priority: str
    review_route: str
    ai_summary: str
    idempotency_key: str


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        return list(reader)


def score_lead(row: dict[str, str]) -> int:
    score = 0
    budget = int(row["budget_usd"])
    timeline = row["timeline"].lower()
    financing = row["financing_status"].lower()
    property_type = row["property_type"].lower()
    consent = row["consent_to_contact"].lower() == "yes"

    if budget >= 150000:
        score += 35
    elif budget >= 75000:
        score += 20
    else:
        score += 5

    if "0-3" in timeline:
        score += 25
    elif "3-6" in timeline:
        score += 18
    else:
        score += 10

    if "preapproved" in financing or "cash" in financing:
        score += 25
    elif "lender" in financing:
        score += 12

    if property_type in {"condo", "single family", "multi-family"}:
        score += 10

    if consent:
        score += 5
    else:
        score -= 35

    return max(score, 0)


def choose_priority(score: int) -> str:
    if score >= 80:
        return "hot"
    if score >= 55:
        return "warm"
    return "review"


def choose_route(row: dict[str, str], score: int) -> str:
    if row["consent_to_contact"].lower() != "yes":
        return "consent_review_queue"
    if row["property_type"].lower() not in {"condo", "single family", "multi-family"}:
        return "not_real_estate_review"
    if score >= 80:
        return "telegram_owner_alert"
    if score >= 55:
        return "weekly_lead_digest"
    return "manual_review_queue"


def summarize(row: dict[str, str], score: int, route: str) -> str:
    return (
        f"{row['contact_name']} is a {choose_priority(score)} lead for {row['city']} "
        f"{row['property_type']} with budget ${int(row['budget_usd']):,}, timeline "
        f"{row['timeline']}, financing status '{row['financing_status']}'. "
        f"Route: {route}. Notes: {row['notes']}"
    )


def build_record(row: dict[str, str]) -> LeadRecord:
    score = score_lead(row)
    route = choose_route(row, score)
    return LeadRecord(
        lead_id=row["lead_id"],
        source_ref=row["source_ref"],
        language=row["language"],
        contact_name=row["contact_name"],
        contact_handle=row["contact_handle"],
        budget_usd=int(row["budget_usd"]),
        city=row["city"],
        property_type=row["property_type"],
        timeline=row["timeline"],
        financing_status=row["financing_status"],
        lead_score=score,
        priority=choose_priority(score),
        review_route=route,
        ai_summary=summarize(row, score, route),
        idempotency_key=f"telegram-lead:{row['lead_id']}:{row['source_ref']}",
    )


def process_leads(input_path: Path) -> list[LeadRecord]:
    rows = read_rows(input_path)
    if not rows:
        raise ValueError(f"No lead rows found in {input_path}")
    return [build_record(row) for row in rows]


def build_telegram_notifications(records: list[LeadRecord]) -> list[dict[str, object]]:
    notifications = []
    for record in records:
        if record.review_route != "telegram_owner_alert":
            continue
        notifications.append(
            {
                "method": "POST",
                "endpoint": "/telegram/sendMessage",
                "headers": {
                    "Idempotency-Key": record.idempotency_key,
                    "X-Dry-Run": "true",
                },
                "body": {
                    "chat_id": "OWNER_CHAT_ID_PLACEHOLDER",
                    "text": (
                        f"Hot lead: {record.contact_name} ({record.contact_handle})\n"
                        f"{record.city} {record.property_type} | score {record.lead_score}\n"
                        f"{record.ai_summary}"
                    ),
                    "parse_mode": "Markdown",
                },
                "status": "dry_run_only",
            }
        )
    return notifications


def build_ai_summary_payloads(records: list[LeadRecord]) -> list[dict[str, object]]:
    payloads = []
    for record in records:
        payloads.append(
            {
                "method": "POST",
                "endpoint": "/llm/lead-summary",
                "headers": {
                    "Idempotency-Key": record.idempotency_key,
                    "X-Dry-Run": "true",
                },
                "body": {
                    "leadId": record.lead_id,
                    "language": record.language,
                    "schema": {
                        "summary": "string",
                        "priority": "hot|warm|review",
                        "nextQuestion": "string",
                    },
                    "input": {
                        "city": record.city,
                        "propertyType": record.property_type,
                        "budgetUsd": record.budget_usd,
                        "timeline": record.timeline,
                        "financingStatus": record.financing_status,
                        "notes": record.ai_summary,
                    },
                },
                "status": "dry_run_only",
            }
        )
    return payloads


def render_acceptance_report(records: list[LeadRecord]) -> str:
    lines = [
        "# Telegram Lead Qualifier MVP Acceptance Report",
        "",
        "Fictional sample output. Telegram, LLM, payment, and CRM calls are staged only.",
        "",
        "| Lead | Source | Contact | Score | Priority | Route |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for record in records:
        lines.append(
            f"| {record.lead_id} | {record.source_ref} | {record.contact_handle} | "
            f"{record.lead_score} | {record.priority} | {record.review_route} |"
        )
    lines.extend(
        [
            "",
            "## First Milestone Acceptance Test",
            "",
            "- User completes a 7-10 question Telegram intake.",
            "- Source/referral code is saved with the lead record.",
            "- Answers are stored in Google Sheets or Supabase-shaped rows.",
            "- Structured AI summary payload is prepared for approved LLM provider.",
            "- Hot leads create a dry-run owner notification payload.",
            "- Non-consenting or off-scope leads route to review instead of outreach.",
            "",
            "## Deferred Until Milestone Two",
            "",
            "- Payment collection.",
            "- CRM writeback.",
            "- Production Telegram bot token.",
            "- Automatic customer-facing follow-up.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def write_outputs(records: list[LeadRecord], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_records = sorted(records, key=lambda item: item.lead_id)

    with (out_dir / "lead_records.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(sorted_records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(record) for record in sorted_records)

    (out_dir / "telegram_notifications.json").write_text(
        json.dumps(build_telegram_notifications(sorted_records), indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "ai_summary_payloads.json").write_text(
        json.dumps(build_ai_summary_payloads(sorted_records), indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "mvp_acceptance_report.md").write_text(
        render_acceptance_report(sorted_records),
        encoding="utf-8",
    )
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "lead_count": len(sorted_records),
                "hot_count": sum(1 for record in sorted_records if record.priority == "hot"),
                "warm_count": sum(1 for record in sorted_records if record.priority == "warm"),
                "review_count": sum(1 for record in sorted_records if record.priority == "review"),
                "dry_run_notifications": len(build_telegram_notifications(sorted_records)),
                "routes": sorted({record.review_route for record in sorted_records}),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a dry-run Telegram lead qualifier MVP pack.")
    parser.add_argument("--input", type=Path, default=Path("input/lead_intake.csv"))
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()

    records = process_leads(args.input)
    write_outputs(records, args.out)


if __name__ == "__main__":
    main()
