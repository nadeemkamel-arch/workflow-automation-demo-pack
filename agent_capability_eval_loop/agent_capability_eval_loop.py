#!/usr/bin/env python3
"""Eval and monitoring loop for fictional capability-agent runs.

The demo keeps all data public-safe. It scores runs against a contract, creates
repair tasks, and writes an owner-readable handoff for the next iteration.
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
    capability: str
    scenario_id: str
    area: str
    problem: str
    recommendation: str


def load_contract(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        return json.load(handle)


def load_runs(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        row["passed"] = row["passed"].lower() == "true"
        row["confidence"] = float(row["confidence"])
        row["citation_coverage"] = float(row["citation_coverage"])
        row["handoff_triggered"] = row["handoff_triggered"].lower() == "true"
        row["latency_ms"] = int(row["latency_ms"])
        row["trace_field_set"] = set(filter(None, row["trace_fields"].split("|")))
    return rows


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
            capability=row["capability"],
            scenario_id=row["scenario_id"],
            area=area,
            problem=problem,
            recommendation=recommendation,
        )
    )


def stable_task_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode()).hexdigest()
    return f"ITER-{digest[:10]}"


def capability_threshold(contract: dict[str, Any], capability: str, key: str) -> Any:
    capability_config = contract.get("capabilities", {}).get(capability, {})
    return capability_config.get(key, contract["global"].get(key))


def review_run(row: dict[str, Any], contract: dict[str, Any], findings: list[Finding]) -> None:
    capability = row["capability"]
    required_fields = set(capability_threshold(contract, capability, "must_have_trace_fields") or [])
    missing_trace_fields = sorted(required_fields - row["trace_field_set"])

    if missing_trace_fields:
        add_finding(
            findings,
            "blocker",
            row,
            "audit_trace",
            f"Missing required trace fields: {', '.join(missing_trace_fields)}.",
            "Add structured trace fields before this capability is used for production decisions.",
        )

    if row["tool_status"] != "ok":
        add_finding(
            findings,
            "high",
            row,
            "tool_reliability",
            f"Tool status was `{row['tool_status']}` for this scenario.",
            "Capture the failing payload, add retry bounds, and hand off after one controlled retry.",
        )

    min_citations = contract["global"]["min_citation_coverage"]
    if row["citation_coverage"] < min_citations:
        add_finding(
            findings,
            "high",
            row,
            "retrieval_evidence",
            f"Citation coverage {row['citation_coverage']:.0%} is below required {min_citations:.0%}.",
            "Require source IDs, quoted spans, or document offsets before presenting the answer as grounded.",
        )

    if not row["passed"]:
        severity = "high" if row["user_feedback"] == "negative" else "medium"
        add_finding(
            findings,
            severity,
            row,
            "eval_failure",
            f"Expected `{row['expected_outcome']}` but observed `{row['actual_outcome']}`.",
            "Add this scenario to the regression set and patch prompt, retrieval, or tool routing before expansion.",
        )

    if row["confidence"] < 0.7 and not row["handoff_triggered"]:
        add_finding(
            findings,
            "medium",
            row,
            "handoff_policy",
            f"Confidence was {row['confidence']:.0%} but no handoff was triggered.",
            "Route low-confidence outputs to human review with a concise uncertainty note.",
        )


def review_runs(runs: list[dict[str, Any]], contract: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for row in runs:
        review_run(row, contract, findings)

    for capability in sorted({row["capability"] for row in runs}):
        capability_rows = [row for row in runs if row["capability"] == capability]
        pass_rate = sum(row["passed"] for row in capability_rows) / len(capability_rows)
        required_pass_rate = capability_threshold(contract, capability, "min_pass_rate")
        if pass_rate < required_pass_rate:
            synthetic = {
                "capability": capability,
                "scenario_id": "capability-rollup",
            }
            findings.append(
                Finding(
                    severity="high",
                    capability=capability,
                    scenario_id=synthetic["scenario_id"],
                    area="capability_health",
                    problem=f"Pass rate {pass_rate:.0%} is below required {required_pass_rate:.0%}.",
                    recommendation="Pause expansion and run a targeted repair sprint against failed and borderline scenarios.",
                )
            )

    return sorted(
        findings,
        key=lambda finding: (
            SEVERITY_ORDER[finding.severity],
            finding.capability,
            finding.scenario_id,
            finding.area,
        ),
    )


def summarize(runs: list[dict[str, Any]], findings: list[Finding], contract: dict[str, Any]) -> dict[str, Any]:
    total = len(runs)
    pass_count = sum(row["passed"] for row in runs)
    tool_errors = sum(row["tool_status"] != "ok" for row in runs)
    negative_feedback = sum(row["user_feedback"] == "negative" for row in runs)
    trace_complete = sum(
        not (set(capability_threshold(contract, row["capability"], "must_have_trace_fields") or []) - row["trace_field_set"])
        for row in runs
    )

    counts_by_severity: dict[str, int] = {}
    counts_by_area: dict[str, int] = {}
    for finding in findings:
        counts_by_severity[finding.severity] = counts_by_severity.get(finding.severity, 0) + 1
        counts_by_area[finding.area] = counts_by_area.get(finding.area, 0) + 1

    pass_rate = pass_count / total
    tool_error_rate = tool_errors / total
    trace_coverage = trace_complete / total
    negative_feedback_rate = negative_feedback / total

    decision = "ready_for_limited_pilot"
    if any(finding.severity == "blocker" for finding in findings):
        decision = "block_pilot"
    elif (
        pass_rate < contract["global"]["min_pass_rate"]
        or tool_error_rate > contract["global"]["max_tool_error_rate"]
        or negative_feedback_rate > contract["global"]["max_negative_feedback_rate"]
    ):
        decision = "repair_before_pilot"

    return {
        "decision": decision,
        "total_runs": total,
        "pass_rate": round(pass_rate, 3),
        "tool_error_rate": round(tool_error_rate, 3),
        "trace_coverage": round(trace_coverage, 3),
        "negative_feedback_rate": round(negative_feedback_rate, 3),
        "counts_by_severity": counts_by_severity,
        "counts_by_area": counts_by_area,
    }


def build_iteration_tasks(findings: list[Finding]) -> list[dict[str, str]]:
    tasks = []
    for finding in findings:
        if finding.severity not in {"blocker", "high"}:
            continue
        task_type = {
            "audit_trace": "instrumentation",
            "tool_reliability": "tooling",
            "retrieval_evidence": "retrieval",
            "eval_failure": "eval_regression",
            "capability_health": "repair_sprint",
        }.get(finding.area, "follow_up")
        tasks.append(
            {
                "task_id": stable_task_id(finding.capability, finding.scenario_id, finding.area),
                "capability": finding.capability,
                "scenario_id": finding.scenario_id,
                "type": task_type,
                "problem": finding.problem,
                "next_step": finding.recommendation,
                "requires_human_review": "true",
            }
        )
    return tasks


def write_outputs(out_dir: Path, runs: list[dict[str, Any]], findings: list[Finding], summary: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "findings.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(findings[0]).keys()) if findings else ["severity", "capability", "scenario_id", "area", "problem", "recommendation"])
        writer.writeheader()
        for finding in findings:
            writer.writerow(asdict(finding))

    tasks = build_iteration_tasks(findings)
    with (out_dir / "iteration_tasks.json").open("w") as handle:
        json.dump(tasks, handle, indent=2)

    with (out_dir / "monitoring_summary.json").open("w") as handle:
        json.dump(summary, handle, indent=2)

    brief_lines = [
        "# Agent Capability Eval Handoff",
        "",
        f"Decision: `{summary['decision']}`",
        f"Runs reviewed: {summary['total_runs']}",
        f"Pass rate: {summary['pass_rate']:.0%}",
        f"Tool error rate: {summary['tool_error_rate']:.0%}",
        f"Trace coverage: {summary['trace_coverage']:.0%}",
        "",
        "## Top Findings",
    ]
    for finding in findings[:8]:
        brief_lines.append(
            f"- [{finding.severity}] {finding.capability}/{finding.scenario_id}: {finding.problem} Recommendation: {finding.recommendation}"
        )
    if not findings:
        brief_lines.append("- No findings above threshold.")
    brief_lines.extend(
        [
            "",
            "## Next Iteration Tasks",
        ]
    )
    for task in tasks[:8]:
        brief_lines.append(f"- {task['task_id']} ({task['type']}): {task['next_step']}")
    if not tasks:
        brief_lines.append("- Keep the pilot limited and continue collecting telemetry.")

    (out_dir / "handoff_brief.md").write_text("\n".join(brief_lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate fictional capability-agent runs.")
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    contract = load_contract(args.contract)
    runs = load_runs(args.runs)
    findings = review_runs(runs, contract)
    summary = summarize(runs, findings, contract)
    write_outputs(args.out, runs, findings, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
