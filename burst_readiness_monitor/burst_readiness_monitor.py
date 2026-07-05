from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_COLUMNS = {
    "window_start",
    "endpoint",
    "requests",
    "p50_ms",
    "p95_ms",
    "p99_ms",
    "errors_5xx",
    "errors_4xx",
    "db_cpu_pct",
    "app_cpu_pct",
    "cache_hit_pct",
    "estimated_cost_usd",
    "owner",
    "dependency",
}


@dataclass(frozen=True)
class EndpointReadiness:
    endpoint: str
    owner: str
    dependency: str
    total_requests: int
    peak_rps: float
    weighted_p95_ms: int
    worst_p99_ms: int
    error_rate_5xx: float
    max_db_cpu_pct: int
    max_app_cpu_pct: int
    min_cache_hit_pct: int
    cost_per_1k_requests_usd: float
    severity: str
    route: str
    recommended_action: str


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        return list(reader)


def _group_by_endpoint(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["endpoint"], []).append(row)
    return grouped


def _weighted_average(rows: list[dict[str, str]], value_field: str) -> int:
    total_requests = sum(int(row["requests"]) for row in rows)
    if total_requests == 0:
        return 0
    weighted = sum(int(row["requests"]) * float(row[value_field]) for row in rows)
    return round(weighted / total_requests)


def _classify(
    *,
    weighted_p95_ms: int,
    worst_p99_ms: int,
    error_rate_5xx: float,
    max_db_cpu_pct: int,
    max_app_cpu_pct: int,
    min_cache_hit_pct: int,
    cost_per_1k_requests_usd: float,
    p95_target_ms: int,
    p99_target_ms: int,
    error_budget: float,
    cost_per_1k_limit: float,
) -> tuple[str, str, str]:
    if error_rate_5xx > error_budget * 2 or max_db_cpu_pct >= 90 or weighted_p95_ms >= p95_target_ms * 1.5:
        return (
            "critical",
            "launch_blocker",
            "pause_scale_up_and_fix_capacity_or_error_source",
        )
    if (
        error_rate_5xx > error_budget
        or max_app_cpu_pct >= 85
        or min_cache_hit_pct < 55
        or weighted_p95_ms > p95_target_ms
        or cost_per_1k_requests_usd > cost_per_1k_limit
    ):
        return (
            "warning",
            "capacity_plan",
            "add_owner_alert_and_retune_before_public_burst",
        )
    if worst_p99_ms > p99_target_ms or min_cache_hit_pct < 70:
        return (
            "notice",
            "monitoring_review",
            "watch_in_next_load_test_and_keep_manual_rollback_ready",
        )
    return ("ok", "ready", "none")


def analyze_endpoints(
    path: Path,
    *,
    window_seconds: int = 60,
    p95_target_ms: int = 500,
    p99_target_ms: int = 1000,
    error_budget: float = 0.005,
    cost_per_1k_limit: float = 0.075,
) -> list[EndpointReadiness]:
    rows = read_rows(path)
    if not rows:
        raise ValueError(f"No traffic rows found in {path}")

    records: list[EndpointReadiness] = []
    for endpoint, endpoint_rows in _group_by_endpoint(rows).items():
        total_requests = sum(int(row["requests"]) for row in endpoint_rows)
        total_5xx = sum(int(row["errors_5xx"]) for row in endpoint_rows)
        total_cost = sum(float(row["estimated_cost_usd"]) for row in endpoint_rows)
        peak_rps = max(int(row["requests"]) / window_seconds for row in endpoint_rows)
        weighted_p95_ms = _weighted_average(endpoint_rows, "p95_ms")
        worst_p99_ms = max(int(row["p99_ms"]) for row in endpoint_rows)
        max_db_cpu_pct = max(int(row["db_cpu_pct"]) for row in endpoint_rows)
        max_app_cpu_pct = max(int(row["app_cpu_pct"]) for row in endpoint_rows)
        min_cache_hit_pct = min(int(row["cache_hit_pct"]) for row in endpoint_rows)
        error_rate_5xx = total_5xx / total_requests if total_requests else 0.0
        cost_per_1k_requests_usd = (total_cost / total_requests * 1000) if total_requests else 0.0

        severity, route, recommended_action = _classify(
            weighted_p95_ms=weighted_p95_ms,
            worst_p99_ms=worst_p99_ms,
            error_rate_5xx=error_rate_5xx,
            max_db_cpu_pct=max_db_cpu_pct,
            max_app_cpu_pct=max_app_cpu_pct,
            min_cache_hit_pct=min_cache_hit_pct,
            cost_per_1k_requests_usd=cost_per_1k_requests_usd,
            p95_target_ms=p95_target_ms,
            p99_target_ms=p99_target_ms,
            error_budget=error_budget,
            cost_per_1k_limit=cost_per_1k_limit,
        )

        first_row = endpoint_rows[0]
        records.append(
            EndpointReadiness(
                endpoint=endpoint,
                owner=first_row["owner"],
                dependency=first_row["dependency"],
                total_requests=total_requests,
                peak_rps=round(peak_rps, 2),
                weighted_p95_ms=weighted_p95_ms,
                worst_p99_ms=worst_p99_ms,
                error_rate_5xx=round(error_rate_5xx, 4),
                max_db_cpu_pct=max_db_cpu_pct,
                max_app_cpu_pct=max_app_cpu_pct,
                min_cache_hit_pct=min_cache_hit_pct,
                cost_per_1k_requests_usd=round(cost_per_1k_requests_usd, 3),
                severity=severity,
                route=route,
                recommended_action=recommended_action,
            )
        )
    return sorted(records, key=lambda record: (record.severity != "critical", record.endpoint))


def peak_total_rps(path: Path, window_seconds: int) -> float:
    rows = read_rows(path)
    by_window: dict[str, int] = {}
    for row in rows:
        by_window[row["window_start"]] = by_window.get(row["window_start"], 0) + int(row["requests"])
    return round(max(by_window.values()) / window_seconds, 2)


def build_alert_payloads(records: list[EndpointReadiness]) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for record in records:
        if record.severity == "ok":
            continue
        payloads.append(
            {
                "method": "POST",
                "endpoint": "/ops/burst-readiness/alerts",
                "headers": {
                    "X-Dry-Run": "true",
                    "Idempotency-Key": f"burst-alert:{record.endpoint}:{record.route}",
                },
                "body": {
                    "endpoint": record.endpoint,
                    "owner": record.owner,
                    "severity": record.severity,
                    "route": record.route,
                    "dependency": record.dependency,
                    "p95Ms": record.weighted_p95_ms,
                    "errorRate5xx": record.error_rate_5xx,
                    "action": record.recommended_action,
                },
                "status": "dry_run_only",
            }
        )
    return payloads


def _count(records: list[EndpointReadiness], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(getattr(record, field_name))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def render_load_test_brief(
    records: list[EndpointReadiness],
    *,
    target_rps: int,
    peak_rps: float,
) -> str:
    lines = [
        "# Burst Readiness Brief",
        "",
        "Fictional sample output for a limited-beta platform preparing for a traffic burst.",
        "Alert, scaling, and rollback actions are dry-run only until a client approves live routing.",
        "",
        f"- Target burst: {target_rps} RPS",
        f"- Observed synthetic peak: {peak_rps} RPS",
        f"- Target met in sample: {'yes' if peak_rps >= target_rps else 'no'}",
        "",
        "| Endpoint | Severity | Peak RPS | p95 ms | 5xx rate | Cost / 1k | Route | Owner |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for record in records:
        lines.append(
            f"| {record.endpoint} | {record.severity} | {record.peak_rps:.2f} | "
            f"{record.weighted_p95_ms} | {record.error_rate_5xx:.4f} | "
            f"${record.cost_per_1k_requests_usd:.3f} | {record.route} | {record.owner} |"
        )
    lines.extend(
        [
            "",
            "## Launch Gates",
            "",
            "- Fix critical endpoint errors or database saturation before promoting traffic.",
            "- Keep autoscale, cache, and queue changes behind a reversible rollout plan.",
            "- Add owner-visible alerts for p95 latency, 5xx rate, worker backlog, and spend per 1k requests.",
            "- Load test again after changes and compare endpoint-level p95, p99, 5xx rate, and cost.",
            "- Do not connect production credentials or live customer messaging until sample checks pass.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def write_outputs(
    records: list[EndpointReadiness],
    out_dir: Path,
    *,
    source_path: Path,
    target_rps: int,
    window_seconds: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_records = sorted(records, key=lambda record: record.endpoint)
    current_peak_total_rps = peak_total_rps(source_path, window_seconds)

    with (out_dir / "endpoint_readiness.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(asdict(sorted_records[0]).keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(asdict(record) for record in sorted_records)

    alert_payloads = build_alert_payloads(sorted_records)
    (out_dir / "alert_payloads.json").write_text(
        json.dumps(alert_payloads, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "load_test_brief.md").write_text(
        render_load_test_brief(sorted_records, target_rps=target_rps, peak_rps=current_peak_total_rps),
        encoding="utf-8",
    )
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "endpoint_count": len(sorted_records),
                "target_rps": target_rps,
                "peak_total_rps": current_peak_total_rps,
                "target_met": current_peak_total_rps >= target_rps,
                "alert_payload_count": len(alert_payloads),
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
    parser = argparse.ArgumentParser(description="Build a dry-run burst readiness monitor pack.")
    parser.add_argument("--input", type=Path, default=Path("input/traffic_windows.csv"))
    parser.add_argument("--out", type=Path, default=Path("output"))
    parser.add_argument("--target-rps", type=int, default=500)
    parser.add_argument("--window-seconds", type=int, default=60)
    args = parser.parse_args()

    records = analyze_endpoints(args.input, window_seconds=args.window_seconds)
    write_outputs(
        records,
        args.out,
        source_path=args.input,
        target_rps=args.target_rps,
        window_seconds=args.window_seconds,
    )


if __name__ == "__main__":
    main()
