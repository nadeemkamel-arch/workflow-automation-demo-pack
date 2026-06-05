from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_COLUMNS = {
    "session_id",
    "week_start",
    "party_a",
    "party_a_email",
    "party_b",
    "party_b_email",
    "external_recipient",
    "external_email",
    "service_code",
    "minutes",
    "amount_usd",
}


@dataclass(frozen=True)
class EmailStatement:
    statement_id: str
    statement_type: str
    week_start: str
    to: str
    cc: str
    subject: str
    total_minutes: int
    total_amount_usd: float
    session_count: int
    body_preview: str
    send_payload_status: str


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        return list(reader)


def build_database(rows: list[dict[str, str]]) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY,
            week_start TEXT NOT NULL,
            party_a TEXT NOT NULL,
            party_a_email TEXT NOT NULL,
            party_b TEXT NOT NULL,
            party_b_email TEXT NOT NULL,
            external_recipient TEXT NOT NULL,
            external_email TEXT NOT NULL,
            service_code TEXT NOT NULL,
            minutes INTEGER NOT NULL,
            amount_usd REAL NOT NULL
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO sessions (
            session_id, week_start, party_a, party_a_email, party_b, party_b_email,
            external_recipient, external_email, service_code, minutes, amount_usd
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["session_id"],
                row["week_start"],
                row["party_a"],
                row["party_a_email"],
                row["party_b"],
                row["party_b_email"],
                row["external_recipient"],
                row["external_email"],
                row["service_code"],
                int(row["minutes"]),
                float(row["amount_usd"]),
            )
            for row in rows
        ],
    )
    return conn


def _statement_body(title: str, rows: list[sqlite3.Row]) -> str:
    lines = [
        title,
        "",
        "| Session | Service | Minutes | Amount |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['session_id']} | {row['service_code']} | "
            f"{row['minutes']} | ${row['amount_usd']:.2f} |"
        )
    lines.extend(
        [
            "",
            "Please review before sending from the approved mail service.",
        ]
    )
    return "\n".join(lines)


def _rows_for_pair(conn: sqlite3.Connection, week_start: str, party_a: str, party_b: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT * FROM sessions
            WHERE week_start = ? AND party_a = ? AND party_b = ?
            ORDER BY session_id
            """,
            (week_start, party_a, party_b),
        )
    )


def _rows_for_external(conn: sqlite3.Connection, week_start: str, external_email: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT * FROM sessions
            WHERE week_start = ? AND external_email = ?
            ORDER BY session_id
            """,
            (week_start, external_email),
        )
    )


def _summarize(rows: list[sqlite3.Row]) -> tuple[int, float]:
    minutes = sum(int(row["minutes"]) for row in rows)
    amount = sum(float(row["amount_usd"]) for row in rows)
    return minutes, amount


def build_pair_statements(conn: sqlite3.Connection) -> list[EmailStatement]:
    groups = conn.execute(
        """
        SELECT week_start, party_a, party_a_email, party_b, party_b_email
        FROM sessions
        GROUP BY week_start, party_a, party_a_email, party_b, party_b_email
        ORDER BY week_start, party_a, party_b
        """
    )
    statements: list[EmailStatement] = []
    for group in groups:
        rows = _rows_for_pair(conn, group["week_start"], group["party_a"], group["party_b"])
        minutes, amount = _summarize(rows)
        statement_id = f"pair:{group['week_start']}:{group['party_a']}:{group['party_b']}".replace(" ", "-")
        body = _statement_body(
            f"Weekly paired statement for {group['party_a']} and {group['party_b']}",
            rows,
        )
        statements.append(
            EmailStatement(
                statement_id=statement_id,
                statement_type="party_pair_weekly",
                week_start=group["week_start"],
                to=f"{group['party_a_email']}, {group['party_b_email']}",
                cc="statements@example.test",
                subject=f"Weekly statement: {group['party_a']} + {group['party_b']} ({group['week_start']})",
                total_minutes=minutes,
                total_amount_usd=amount,
                session_count=len(rows),
                body_preview=body,
                send_payload_status="dry_run_only",
            )
        )
    return statements


def build_external_statements(conn: sqlite3.Connection) -> list[EmailStatement]:
    groups = conn.execute(
        """
        SELECT week_start, external_recipient, external_email
        FROM sessions
        GROUP BY week_start, external_recipient, external_email
        ORDER BY week_start, external_recipient
        """
    )
    statements: list[EmailStatement] = []
    for group in groups:
        rows = _rows_for_external(conn, group["week_start"], group["external_email"])
        minutes, amount = _summarize(rows)
        statement_id = f"external:{group['week_start']}:{group['external_email']}".replace(" ", "-")
        body = _statement_body(
            f"Weekly external statement for {group['external_recipient']}",
            rows,
        )
        statements.append(
            EmailStatement(
                statement_id=statement_id,
                statement_type="external_recipient_weekly",
                week_start=group["week_start"],
                to=group["external_email"],
                cc="ops@example.test, billing@example.test",
                subject=f"Weekly statement for {group['external_recipient']} ({group['week_start']})",
                total_minutes=minutes,
                total_amount_usd=amount,
                session_count=len(rows),
                body_preview=body,
                send_payload_status="dry_run_only",
            )
        )
    return statements


def build_send_payload(statement: EmailStatement) -> dict[str, object]:
    return {
        "provider": "example-mail-service",
        "method": "POST",
        "endpoint": "/messages/send",
        "headers": {
            "Idempotency-Key": statement.statement_id,
            "X-Dry-Run": "true",
        },
        "body": {
            "to": [email.strip() for email in statement.to.split(",")],
            "cc": [email.strip() for email in statement.cc.split(",")],
            "subject": statement.subject,
            "markdownBody": statement.body_preview,
        },
    }


def build_statements(input_path: Path) -> list[EmailStatement]:
    rows = read_rows(input_path)
    with build_database(rows) as conn:
        return build_pair_statements(conn) + build_external_statements(conn)


def render_preview(statements: list[EmailStatement]) -> str:
    lines = [
        "# Statement Email Preview",
        "",
        "Fictional dry-run output. No email is sent.",
        "",
        "| Type | Week | To | CC | Sessions | Minutes | Amount |",
        "| --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for statement in statements:
        lines.append(
            f"| {statement.statement_type} | {statement.week_start} | {statement.to} | "
            f"{statement.cc} | {statement.session_count} | {statement.total_minutes} | "
            f"${statement.total_amount_usd:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Launch Gate",
            "",
            "- Confirm SQL against the real PostgreSQL schema.",
            "- Send to test recipients before enabling the schedule.",
            "- Log each statement with an idempotency key before live send.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def write_outputs(statements: list[EmailStatement], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_statements = sorted(statements, key=lambda item: item.statement_id)
    payloads = [build_send_payload(statement) for statement in sorted_statements]
    dry_run_log = [
        {
            "statement_id": statement.statement_id,
            "status": "not_sent",
            "reason": "dry_run_only",
            "recipient_count": len(build_send_payload(statement)["body"]["to"]),
        }
        for statement in sorted_statements
    ]

    (out_dir / "statement_preview.md").write_text(render_preview(sorted_statements), encoding="utf-8")
    (out_dir / "email_send_payloads.json").write_text(json.dumps(payloads, indent=2), encoding="utf-8")
    (out_dir / "dry_run_log.json").write_text(json.dumps(dry_run_log, indent=2), encoding="utf-8")
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "total_statements": len(sorted_statements),
                "by_statement_type": _count_by(sorted_statements, "statement_type"),
                "total_amount_usd": round(sum(item.total_amount_usd for item in sorted_statements), 2),
                "send_mode": "dry_run_only",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _count_by(statements: list[EmailStatement], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for statement in statements:
        value = str(getattr(statement, field_name))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build dry-run weekly statement emails from fictional session records."
    )
    parser.add_argument("--input", type=Path, required=True, help="CSV file of fictional session records.")
    parser.add_argument("--out", type=Path, required=True, help="Directory for generated output files.")
    args = parser.parse_args()

    statements = build_statements(args.input)
    write_outputs(statements, args.out)
    print(f"Built {len(statements)} dry-run statement payloads at {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
