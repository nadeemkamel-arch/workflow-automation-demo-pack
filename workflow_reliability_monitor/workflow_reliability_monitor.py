from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_COLUMNS = {
    "run_id",
    "workflow",
    "started_at",
    "duration_sec",
    "status",
    "attempt",
    "max_attempts",
    "idempotency_key",
    "owner",
    "error_code",
}

RETRYABLE_ERRORS = {"RATE_LIMIT", "TIMEOUT", "TEMPORARY_UPSTREAM"}


@dataclass(frozen=True)
class RunHealth:
    run_id: str
    workflow: str
    status: str
    duration_sec: int
    attempt: int
    max_attempts: int
    idempotency_key: str
    owner: str
    error_code: str
    severity: str
    route: str
    action: str


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        return list(reader)


def _duplicate_keys(rows: list[dict[str, str]]) -> set[str]:
    counts: dict[str, int] = {}
    for row in rows:
        key = row["idempotency_key"]
        counts[key] = counts.get(key, 0) + 1
    return {key for key, count in counts.items() if count > 1}


def classify_row(row: dict[str, str], duplicate_keys: set[str], slow_threshold: int) -> RunHealth:
    duration = int(row["duration_sec"])
    attempt = int(row["attempt"])
    max_attempts = int(row["max_attempts"])
    status = row["status"].lower()
    error_code = row["error_code"]
    duplicate = row["idempotency_key"] in duplicate_keys

    if status == "failed" and (attempt >= max_attempts or error_code not in RETRYABLE_ERRORS):
        severity = "critical"
        route = "incident_review"
        action = "page_owner_and_pause_workflow"
    elif status == "failed":
        severity = "warning"
        route = "retry_queue"
        action = "schedule_retry_with_backoff"
    elif duplicate:
        severity = "warning"
        route = "idempotency_review"
        action = "verify_duplicate_was_deduped"
    elif duration >= slow_threshold:
        severity = "notice"
        route = "performance_review"
        action = "inspect_slow_run"
    else:
        severity = "ok"
        route = "healthy"
        action = "none"

    return RunHealth(
        run_id=row["run_id"],
        workflow=row["workflow"],
        status=status,
        duration_sec=duration,
        attempt=attempt,
        max_attempts=max_attempts,
        idempotency_key=row["idempotency_key"],
        owner=row["owner"],
        error_code=error_code,
        severity=severity,
        route=route,
        action=action,
    )


def analyze_runs(path: Path, slow_threshold: int = 120) -> list[RunHealth]:
    rows = read_rows(path)
    if not rows:
        raise ValueError(f"No workflow run rows found in {path}")
    duplicates = _duplicate_keys(rows)
    return [classify_row(row, duplicates, slow_threshold) for row in rows]


def build_retry_payloads(records: list[RunHealth]) -> list[dict[str, object]]:
    payloads = []
    for record in records:
        if record.route != "retry_queue":
            continue
        payloads.append(
            {
                "method": "POST",
                "endpoint": "/ops/workflow-retries",
                "headers": {
                    "Idempotency-Key": f"retry:{record.idempotency_key}:{record.attempt + 1}",
                    "X-Dry-Run": "true",
                },
                "body": {
                    "runId": record.run_id,
                    "workflow": record.workflow,
                    "nextAttempt": record.attempt + 1,
                    "maxAttempts": record.max_attempts,
                    "reason": record.error_code,
                    "owner": record.owner,
                },
                "status": "dry_run_only",
            }
        )
    return payloads


def _count(records: list[RunHealth], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(getattr(record, field_name))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def render_incident_digest(records: list[RunHealth]) -> str:
    lines = [
        "# Workflow Reliability Incident Digest",
        "",
        "Fictional sample output. Retry, alert, and pause actions are dry-run only.",
        "",
        "| Run | Workflow | Severity | Route | Owner | Action | Error |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        if record.severity == "ok":
            continue
        lines.append(
            f"| {record.run_id} | {record.workflow} | {record.severity} | {record.route} | "
            f"{record.owner} | {record.action} | {record.error_code or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Launch Gate",
            "",
            "- Confirm which failures are retryable before enabling automatic retry.",
            "- Keep destructive or customer-facing actions behind a pause-and-review route.",
            "- Require idempotency keys on every write path.",
            "- Send owner alerts to Slack, email, or PagerDuty only after sample runs pass.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def write_outputs(records: list[RunHealth], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_records = sorted(records, key=lambda record: record.run_id)

    with (out_dir / "run_health.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(sorted_records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(record) for record in sorted_records)

    (out_dir / "retry_payloads.json").write_text(
        json.dumps(build_retry_payloads(sorted_records), indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "incident_digest.md").write_text(
        render_incident_digest(sorted_records),
        encoding="utf-8",
    )

    success_count = sum(1 for record in sorted_records if record.status == "succeeded")
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "run_count": len(sorted_records),
                "success_count": success_count,
                "success_rate": round(success_count / len(sorted_records), 3),
                "retry_payload_count": len(build_retry_payloads(sorted_records)),
                "severity_counts": _count(sorted_records, "severity"),
                "route_counts": _count(sorted_records, "route"),
                "owner_counts": _count(sorted_records, "owner"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a dry-run workflow reliability monitor pack.")
    parser.add_argument("--input", type=Path, default=Path("input/flow_runs.csv"))
    parser.add_argument("--out", type=Path, default=Path("output"))
    parser.add_argument("--slow-threshold", type=int, default=120)
    args = parser.parse_args()

    records = analyze_runs(args.input, slow_threshold=args.slow_threshold)
    write_outputs(records, args.out)


if __name__ == "__main__":
    main()
