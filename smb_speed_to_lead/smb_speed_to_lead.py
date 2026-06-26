from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path


NATIVE_CRM_NODES = {
    "GoHighLevel": "n8n-nodes-base.goHighLevel",
    "HubSpot": "n8n-nodes-base.hubspot",
}

NEW_LEAD_COLUMNS = {
    "lead_id",
    "source",
    "contact_name",
    "email",
    "phone",
    "created_at",
    "crm_type",
    "interest",
    "consent_email",
    "consent_sms",
    "notes",
}

DORMANT_COLUMNS = {
    "contact_id",
    "contact_name",
    "email",
    "phone",
    "crm_type",
    "last_engaged_days",
    "consent_email",
    "consent_sms",
    "opt_out",
    "last_offer",
    "notes",
}


@dataclass(frozen=True)
class ActionRecord:
    record_id: str
    workflow: str
    contact_name: str
    crm_type: str
    crm_adapter: str
    route: str
    allowed_channels: str
    stop_reason: str
    idempotency_key: str


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(missing)}")
        return list(reader)


def yes(value: str) -> bool:
    return value.strip().lower() == "yes"


def crm_adapter(crm_type: str) -> str:
    node = NATIVE_CRM_NODES.get(crm_type)
    if node:
        return f"native:{node}"
    return "http_webhook:generic_adapter"


def allowed_channels(row: dict[str, str]) -> list[str]:
    channels = []
    if yes(row.get("consent_email", "")):
        channels.append("email")
    if yes(row.get("consent_sms", "")):
        channels.append("sms")
    return channels


def speed_to_lead_route(row: dict[str, str]) -> tuple[str, str]:
    channels = allowed_channels(row)
    if not channels:
        return "manual_review_only", "no_outbound_consent"

    text = f"{row['interest']} {row['notes']}".lower()
    if any(term in text for term in ["tomorrow", "this week", "earliest", "book", "appointment", "consult"]):
        return "book_or_owner_alert", "high_intent"
    return "qualify_reply", "needs_qualification"


def dormant_route(row: dict[str, str]) -> tuple[str, str]:
    if yes(row["opt_out"]):
        return "suppress_all_outbound", "opt_out"
    channels = allowed_channels(row)
    if not channels:
        return "manual_review_only", "no_outbound_consent"
    if int(row["last_engaged_days"]) < 90:
        return "wait_until_dormant_window", "not_dormant_yet"
    return "reactivation_sequence", "dormant_contact"


def build_speed_records(rows: list[dict[str, str]]) -> list[ActionRecord]:
    records = []
    for row in rows:
        route, stop_reason = speed_to_lead_route(row)
        channels = allowed_channels(row)
        records.append(
            ActionRecord(
                record_id=row["lead_id"],
                workflow="speed_to_lead",
                contact_name=row["contact_name"],
                crm_type=row["crm_type"],
                crm_adapter=crm_adapter(row["crm_type"]),
                route=route,
                allowed_channels=",".join(channels) if channels else "none",
                stop_reason=stop_reason,
                idempotency_key=f"speed-to-lead:{row['lead_id']}:{row['created_at']}",
            )
        )
    return records


def build_reactivation_records(rows: list[dict[str, str]]) -> list[ActionRecord]:
    records = []
    for row in rows:
        route, stop_reason = dormant_route(row)
        channels = allowed_channels(row)
        records.append(
            ActionRecord(
                record_id=row["contact_id"],
                workflow="database_reactivation",
                contact_name=row["contact_name"],
                crm_type=row["crm_type"],
                crm_adapter=crm_adapter(row["crm_type"]),
                route=route,
                allowed_channels=",".join(channels) if channels else "none",
                stop_reason=stop_reason,
                idempotency_key=f"reactivation:{row['contact_id']}:{row['last_engaged_days']}",
            )
        )
    return records


def build_payloads(records: list[ActionRecord]) -> list[dict[str, object]]:
    payloads = []
    for record in records:
        if record.route in {"manual_review_only", "suppress_all_outbound", "wait_until_dormant_window"}:
            payloads.append(
                {
                    "status": "blocked_before_outbound",
                    "record_id": record.record_id,
                    "workflow": record.workflow,
                    "route": record.route,
                    "reason": record.stop_reason,
                    "idempotency_key": record.idempotency_key,
                }
            )
            continue

        payloads.append(
            {
                "status": "dry_run_only",
                "method": "POST",
                "endpoint": "/client-adapter/send-or-route",
                "headers": {
                    "Idempotency-Key": record.idempotency_key,
                    "X-Dry-Run": "true",
                },
                "body": {
                    "recordId": record.record_id,
                    "workflow": record.workflow,
                    "contactName": record.contact_name,
                    "channels": record.allowed_channels.split(","),
                    "crmAdapter": record.crm_adapter,
                    "route": record.route,
                    "stopOn": ["reply_detected", "opt_out", "booking_created", "manual_owner_stop"],
                    "retryPolicy": {"maxAttempts": 3, "backoffSeconds": [30, 120, 300]},
                },
            }
        )
    return payloads


def write_csv(path: Path, records: list[ActionRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)


def render_config_handoff(speed_records: list[ActionRecord], reactivation_records: list[ActionRecord]) -> str:
    all_records = speed_records + reactivation_records
    http_count = sum(record.crm_adapter.startswith("http_webhook") for record in all_records)
    blocked = [record for record in all_records if record.route in {"manual_review_only", "suppress_all_outbound"}]
    return "\n".join(
        [
            "# SMB Speed-to-Lead Template Handoff",
            "",
            "Fictional sample output. No SMS, email, CRM, or AI provider calls were sent.",
            "",
            "## Reuse Pattern",
            "",
            "- Swap credentials and endpoint env vars in `config.example.json`.",
            "- Keep client-specific text, offers, and CRM status names in config.",
            "- Use native n8n nodes where available; use the HTTP webhook adapter when no native node exists.",
            "- Keep `X-Dry-Run` enabled until the client approves test records and stop rules.",
            "",
            "## Stop Logic",
            "",
            "- No email/SMS consent routes to manual review.",
            "- Opt-out suppresses all outbound attempts.",
            "- Reply, opt-out, booking, or owner stop cancels the remaining sequence.",
            "- Failed CRM or provider calls retry three times, then route to owner review.",
            "",
            "## Run Summary",
            "",
            f"- Speed-to-lead records: {len(speed_records)}",
            f"- Reactivation records: {len(reactivation_records)}",
            f"- Generic HTTP adapter records: {http_count}",
            f"- Blocked before outbound: {len(blocked)}",
        ]
    )


def run(new_leads: Path, dormant_contacts: Path, out: Path) -> dict[str, object]:
    speed_records = build_speed_records(read_csv(new_leads, NEW_LEAD_COLUMNS))
    reactivation_records = build_reactivation_records(read_csv(dormant_contacts, DORMANT_COLUMNS))
    all_records = speed_records + reactivation_records

    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "speed_to_lead_queue.csv", speed_records)
    write_csv(out / "reactivation_queue.csv", reactivation_records)
    (out / "dry_run_payloads.json").write_text(json.dumps(build_payloads(all_records), indent=2), encoding="utf-8")
    (out / "config_handoff.md").write_text(render_config_handoff(speed_records, reactivation_records), encoding="utf-8")

    summary = {
        "speed_to_lead_records": len(speed_records),
        "reactivation_records": len(reactivation_records),
        "dry_run_payloads": len(all_records),
        "blocked_before_outbound": sum(
            record.route in {"manual_review_only", "suppress_all_outbound", "wait_until_dormant_window"}
            for record in all_records
        ),
        "http_webhook_adapter_records": sum(record.crm_adapter.startswith("http_webhook") for record in all_records),
        "live_actions": 0,
    }
    (out / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-leads", type=Path, required=True)
    parser.add_argument("--dormant-contacts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summary = run(args.new_leads, args.dormant_contacts, args.out)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
