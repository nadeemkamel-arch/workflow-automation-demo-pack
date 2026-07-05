#!/usr/bin/env python3
"""Quality gate for agent-generated data pipelines.

The demo uses fictional source runs. It is built for cases where coding agents
generate or repair ETL/RAG/web-data pipelines, but humans still need schema,
source-evidence, drift, and write-safety gates before trusting the dataset.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SEVERITY_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}


@dataclass(frozen=True)
class Finding:
    severity: str
    dataset: str
    source_id: str
    area: str
    problem: str
    recommendation: str
    owner: str


def load_contract(path: Path) -> dict[str, dict[str, Any]]:
    with path.open() as handle:
        return json.load(handle)


def load_runs(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["expected_rows"] = int(row["expected_rows"])
        row["observed_rows"] = int(row["observed_rows"])
        row["duplicate_key_count"] = int(row["duplicate_key_count"])
        row["null_rate"] = float(row["null_rate"])
        row["citation_coverage"] = float(row["citation_coverage"])
        row["http_status"] = int(row["http_status"])
        row["content_hash_changed"] = row["content_hash_changed"].lower() == "true"
        row["last_success_hours"] = int(row["last_success_hours"])
        row["external_write"] = row["external_write"].lower() == "true"
    return rows


def stable_key(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode()).hexdigest()
    return digest[:16]


def add_finding(
    findings: list[Finding],
    severity: str,
    row: dict[str, Any],
    area: str,
    problem: str,
    recommendation: str,
) -> None:
    findings.append(
        Finding(
            severity=severity,
            dataset=row["dataset"],
            source_id=row["source_id"],
            area=area,
            problem=problem,
            recommendation=recommendation,
            owner=row["owner"],
        )
    )


def row_delta_ratio(row: dict[str, Any]) -> float:
    expected = max(row["expected_rows"], 1)
    return abs(row["observed_rows"] - row["expected_rows"]) / expected


def review_run(row: dict[str, Any], contract: dict[str, Any], findings: list[Finding]) -> None:
    observed_fields = set(row["observed_fields"].split("|"))
    required_fields = set(contract["required_fields"])
    missing = sorted(required_fields - observed_fields)
    unexpected = sorted(observed_fields - required_fields)

    if row["http_status"] in {401, 403}:
        add_finding(
            findings,
            "blocker",
            row,
            "access",
            f"Source returned HTTP {row['http_status']}, so the latest run cannot be trusted.",
            "Pause downstream refresh, verify allowed access, and rerun from a sanctioned source export or approved connector.",
        )
    elif row["http_status"] >= 500:
        add_finding(
            findings,
            "high",
            row,
            "access",
            f"Source returned HTTP {row['http_status']}.",
            "Retry with backoff and keep the previous known-good dataset active until a clean run passes.",
        )

    if missing:
        add_finding(
            findings,
            "blocker",
            row,
            "schema",
            f"Missing required fields: {', '.join(missing)}.",
            "Regenerate or patch the extractor, then run schema tests before publishing the dataset.",
        )

    if unexpected:
        add_finding(
            findings,
            "medium",
            row,
            "schema",
            f"Observed unexpected fields: {', '.join(unexpected)}.",
            "Quarantine new fields until they are mapped to the contract or intentionally ignored.",
        )

    if row["primary_key"] != contract["primary_key"]:
        add_finding(
            findings,
            "high",
            row,
            "schema",
            f"Primary key changed from contract `{contract['primary_key']}` to `{row['primary_key']}`.",
            "Block merge and reconcile key semantics before dedupe or upsert logic runs.",
        )

    delta = row_delta_ratio(row)
    if delta > contract["max_row_delta_ratio"]:
        severity = "blocker" if row["observed_rows"] == 0 else "high"
        add_finding(
            findings,
            severity,
            row,
            "volume",
            f"Observed row count changed by {delta:.1%} versus expected {row['expected_rows']}.",
            "Compare source markup/API shape, sample rejected rows, and keep downstream consumers on the last accepted run.",
        )

    if row["duplicate_key_count"] > 0:
        severity = "high" if row["duplicate_key_count"] > 10 else "medium"
        add_finding(
            findings,
            severity,
            row,
            "dedupe",
            f"Found {row['duplicate_key_count']} duplicate primary keys.",
            "Add deterministic dedupe and provider/source timestamps before any upsert or customer-visible export.",
        )

    if row["null_rate"] > contract["max_null_rate"]:
        add_finding(
            findings,
            "high",
            row,
            "quality",
            f"Null rate {row['null_rate']:.1%} exceeds limit {contract['max_null_rate']:.1%}.",
            "Trace nulls by field and source section; rerun only after the extraction rule or fallback is fixed.",
        )

    if row["citation_coverage"] < contract["min_citation_coverage"]:
        add_finding(
            findings,
            "high",
            row,
            "evidence",
            f"Citation/source coverage {row['citation_coverage']:.1%} is below required {contract['min_citation_coverage']:.1%}.",
            "Do not let agent-generated values into review queues without source URLs, row evidence, or document offsets.",
        )

    if row["content_hash_changed"] and delta > 0.05:
        add_finding(
            findings,
            "high",
            row,
            "drift",
            "Source content changed and row volume moved materially in the same run.",
            "Open an extractor-repair task with before/after samples and require a human review before auto-healing.",
        )

    if row["last_success_hours"] > 24:
        add_finding(
            findings,
            "medium",
            row,
            "freshness",
            f"Last accepted run is {row['last_success_hours']} hours old.",
            "Mark the dataset stale and notify the owner if the next repair attempt fails.",
        )

    if row["external_write"] and not contract.get("external_write_allowed"):
        add_finding(
            findings,
            "blocker",
            row,
            "write_gate",
            "Pipeline is configured for external writes, but the dataset contract forbids it.",
            "Switch to dry-run export only until the owner explicitly approves write targets and rollback.",
        )


def review_runs(runs: list[dict[str, Any]], contracts: dict[str, dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    for row in runs:
        contract = contracts.get(row["dataset"])
        if not contract:
            add_finding(
                findings,
                "blocker",
                row,
                "contract",
                "Dataset has no schema contract.",
                "Create a schema, quality, citation, and write-safety contract before accepting runs.",
            )
            continue
        review_run(row, contract, findings)
    return sorted(findings, key=lambda item: (SEVERITY_ORDER[item.severity], item.dataset, item.source_id, item.area))


def summarize(runs: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
    counts = {severity: 0 for severity in SEVERITY_ORDER}
    by_dataset: dict[str, int] = {}
    by_area: dict[str, int] = {}
    for finding in findings:
        counts[finding.severity] += 1
        by_dataset[finding.dataset] = by_dataset.get(finding.dataset, 0) + 1
        by_area[finding.area] = by_area.get(finding.area, 0) + 1

    if counts["blocker"]:
        decision = "pause_affected_datasets"
    elif counts["high"]:
        decision = "repair_before_publish"
    else:
        decision = "publish_candidate"

    return {
        "decision": decision,
        "source_count": len(runs),
        "finding_count": len(findings),
        "counts_by_severity": counts,
        "counts_by_dataset": dict(sorted(by_dataset.items())),
        "counts_by_area": dict(sorted(by_area.items())),
    }


def build_repair_payloads(findings: list[Finding]) -> list[dict[str, Any]]:
    payloads = []
    for finding in findings:
        if finding.severity not in {"blocker", "high"}:
            continue
        payloads.append(
            {
                "idempotency_key": stable_key(finding.dataset, finding.source_id, finding.area, finding.problem),
                "source_id": finding.source_id,
                "dataset": finding.dataset,
                "owner": finding.owner,
                "severity": finding.severity,
                "area": finding.area,
                "agent_task": finding.recommendation,
                "allowed_mode": "dry_run_patch_or_sample_diff",
                "requires_human_review": True,
            }
        )
    return payloads


def write_outputs(runs: list[dict[str, Any]], findings: list[Finding], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(runs, findings)

    with (out_dir / "findings.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(findings[0]).keys()) if findings else ["severity"])
        writer.writeheader()
        for finding in findings:
            writer.writerow(asdict(finding))

    with (out_dir / "repair_payloads.json").open("w") as handle:
        json.dump(build_repair_payloads(findings), handle, indent=2)
        handle.write("\n")

    with (out_dir / "run_summary.json").open("w") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")

    lines = [
        "# Agentic Data Pipeline Gate",
        "",
        f"Decision: `{summary['decision']}`",
        f"Sources reviewed: {summary['source_count']}",
        f"Findings: {summary['finding_count']}",
        "",
        "## Severity Counts",
        "",
    ]
    for severity, count in summary["counts_by_severity"].items():
        lines.append(f"- {severity}: {count}")
    lines.extend(["", "## Top Repair Items", ""])
    for finding in findings[:8]:
        lines.append(
            f"- **{finding.severity} / {finding.dataset} / {finding.source_id} / {finding.area}**: "
            f"{finding.problem} {finding.recommendation}"
        )
    lines.extend(
        [
            "",
            "## Launch Gate",
            "",
            "Keep affected datasets paused until blocker and high findings are resolved. Agent-generated repairs should produce sample diffs, schema-test results, and cited source evidence before any downstream write or customer-visible export.",
        ]
    )
    (out_dir / "validation_report.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Review agent-generated data pipeline runs.")
    parser.add_argument("--runs", type=Path, default=Path("input/source_runs.csv"))
    parser.add_argument("--contract", type=Path, default=Path("input/schema_contract.json"))
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()

    runs = load_runs(args.runs)
    contracts = load_contract(args.contract)
    findings = review_runs(runs, contracts)
    write_outputs(runs, findings, args.out)
    print(json.dumps(summarize(runs, findings), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
