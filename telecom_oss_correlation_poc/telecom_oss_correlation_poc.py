from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_WINDOW_MINUTES = 20


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    section_id: str
    opened_at: datetime
    voltage_drop_pct: int
    status: str


@dataclass(frozen=True)
class Alarm:
    alarm_id: str
    equipment_id: str
    alarm_type: str
    section_id: str
    area: str
    site_name: str
    raised_at: datetime
    severity: str


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def read_tickets(path: Path) -> list[Ticket]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            Ticket(
                ticket_id=row["ticket_id"],
                section_id=row["section_hint"].strip().upper(),
                opened_at=parse_time(row["opened_at"]),
                voltage_drop_pct=int(row["voltage_drop_pct"]),
                status=row["status"],
            )
            for row in csv.DictReader(handle)
        ]


def read_gis(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["equipment_id"]: row for row in csv.DictReader(handle)}


def read_alarms(path: Path, gis_map: dict[str, dict[str, str]]) -> list[Alarm]:
    alarms: list[Alarm] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            gis_row = gis_map.get(row["equipment_id"], {})
            alarms.append(
                Alarm(
                    alarm_id=row["alarm_id"],
                    equipment_id=row["equipment_id"],
                    alarm_type=row["alarm_type"],
                    section_id=gis_row.get("section_id", "UNMAPPED"),
                    area=gis_row.get("area", "Unknown"),
                    site_name=gis_row.get("site_name", "Unknown"),
                    raised_at=parse_time(row["raised_at"]),
                    severity=row["severity"],
                )
            )
    return alarms


def confidence_for(delta_minutes: int, ticket: Ticket, alarm: Alarm) -> str:
    if alarm.section_id == "UNMAPPED":
        return "review"
    if delta_minutes <= 10 and alarm.severity == "critical" and ticket.voltage_drop_pct >= 30:
        return "high"
    if delta_minutes <= DEFAULT_WINDOW_MINUTES:
        return "medium"
    return "review"


def recommended_action(confidence: str) -> str:
    if confidence == "high":
        return "prepare linked-ticket note for owner approval"
    if confidence == "medium":
        return "queue for operator review"
    return "do not update ticket; inspect mapping or timing first"


def correlate(tickets: list[Ticket], alarms: list[Alarm], window_minutes: int) -> tuple[list[dict[str, str]], set[str], set[str]]:
    results: list[dict[str, str]] = []
    matched_tickets: set[str] = set()
    matched_alarms: set[str] = set()

    for ticket in tickets:
        for alarm in alarms:
            if ticket.section_id != alarm.section_id:
                continue

            delta_minutes = round(abs((alarm.raised_at - ticket.opened_at).total_seconds()) / 60)
            if delta_minutes > window_minutes:
                continue

            confidence = confidence_for(delta_minutes, ticket, alarm)
            results.append(
                {
                    "correlation_id": f"{ticket.ticket_id}_{alarm.alarm_id}",
                    "ticket_id": ticket.ticket_id,
                    "alarm_id": alarm.alarm_id,
                    "section_id": ticket.section_id,
                    "site_name": alarm.site_name,
                    "area": alarm.area,
                    "ticket_opened_at": ticket.opened_at.isoformat(timespec="minutes"),
                    "alarm_raised_at": alarm.raised_at.isoformat(timespec="minutes"),
                    "delta_minutes": str(delta_minutes),
                    "alarm_type": alarm.alarm_type,
                    "severity": alarm.severity,
                    "confidence": confidence,
                    "recommended_action": recommended_action(confidence),
                }
            )
            matched_tickets.add(ticket.ticket_id)
            matched_alarms.add(alarm.alarm_id)

    results.sort(key=lambda row: (row["confidence"] != "high", int(row["delta_minutes"]), row["ticket_id"]))
    return results, matched_tickets, matched_alarms


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "correlation_id",
        "ticket_id",
        "alarm_id",
        "section_id",
        "site_name",
        "area",
        "ticket_opened_at",
        "alarm_raised_at",
        "delta_minutes",
        "alarm_type",
        "severity",
        "confidence",
        "recommended_action",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_digest(path: Path, rows: list[dict[str, str]], unmatched_tickets: list[str], unmatched_alarms: list[str]) -> None:
    high = [row for row in rows if row["confidence"] == "high"]
    medium = [row for row in rows if row["confidence"] == "medium"]
    lines = [
        "# Operator Digest",
        "",
        f"- Correlations found: {len(rows)}",
        f"- High confidence: {len(high)}",
        f"- Medium confidence: {len(medium)}",
        f"- Unmatched tickets: {', '.join(unmatched_tickets) if unmatched_tickets else 'none'}",
        f"- Unmatched alarms: {', '.join(unmatched_alarms) if unmatched_alarms else 'none'}",
        "- Live ticket updates: 0",
        "",
        "## Review Queue",
        "",
    ]
    for row in rows:
        lines.append(
            f"- {row['ticket_id']} + {row['alarm_id']} at {row['site_name']} "
            f"({row['confidence']}, {row['delta_minutes']} min): {row['recommended_action']}."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(tickets_path: Path, alarms_path: Path, gis_path: Path, out_dir: Path, window_minutes: int) -> dict[str, object]:
    tickets = read_tickets(tickets_path)
    gis_map = read_gis(gis_path)
    alarms = read_alarms(alarms_path, gis_map)
    rows, matched_tickets, matched_alarms = correlate(tickets, alarms, window_minutes)

    out_dir.mkdir(parents=True, exist_ok=True)
    unmatched_tickets = sorted({ticket.ticket_id for ticket in tickets} - matched_tickets)
    unmatched_alarms = sorted({alarm.alarm_id for alarm in alarms} - matched_alarms)

    write_csv(out_dir / "correlation_results.csv", rows)
    write_digest(out_dir / "operator_digest.md", rows, unmatched_tickets, unmatched_alarms)

    summary = {
        "tickets_seen": len(tickets),
        "alarms_seen": len(alarms),
        "correlations_found": len(rows),
        "high_confidence": sum(1 for row in rows if row["confidence"] == "high"),
        "medium_confidence": sum(1 for row in rows if row["confidence"] == "medium"),
        "unmatched_tickets": unmatched_tickets,
        "unmatched_alarms": unmatched_alarms,
        "live_ticket_updates": 0,
        "window_minutes": window_minutes,
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Correlate telecom OSS power-dip tickets with RFMS alarms.")
    parser.add_argument("--tickets", type=Path, required=True)
    parser.add_argument("--alarms", type=Path, required=True)
    parser.add_argument("--gis", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--window-minutes", type=int, default=DEFAULT_WINDOW_MINUTES)
    args = parser.parse_args()

    summary = run(args.tickets, args.alarms, args.gis, args.out, args.window_minutes)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
