#!/usr/bin/env python3
"""Contract monitor for search-result API snapshots.

The demo uses fictional snapshots and no live scraping. It models the kind of
small quality gate that catches parser regressions before customers see broken
search API responses.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SEVERITY_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}


@dataclass(frozen=True)
class Finding:
    severity: str
    ticket_id: str
    engine: str
    query: str
    area: str
    problem: str
    recommendation: str


def load_contract(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        return json.load(handle)


def load_snapshots(path: Path) -> list[dict[str, Any]]:
    with path.open() as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Snapshots file must contain a list of response snapshots.")
    return data


def ticket_id(snapshot: dict[str, Any]) -> str:
    ticket = snapshot.get("customer_ticket") or {}
    return str(ticket.get("id", "untracked"))


def add_finding(
    findings: list[Finding],
    severity: str,
    snapshot: dict[str, Any],
    area: str,
    problem: str,
    recommendation: str,
) -> None:
    findings.append(
        Finding(
            severity=severity,
            ticket_id=ticket_id(snapshot),
            engine=str(snapshot.get("engine", "unknown")),
            query=str(snapshot.get("query", "")),
            area=area,
            problem=problem,
            recommendation=recommendation,
        )
    )


def validate_top_level(snapshot: dict[str, Any], contract: dict[str, Any], findings: list[Finding]) -> None:
    required = set(contract["required_top_level"])
    missing = sorted(required - set(snapshot))
    if missing:
        add_finding(
            findings,
            "blocker",
            snapshot,
            "shape",
            f"Missing required top-level block(s): {', '.join(missing)}.",
            "Patch the parser mapping or route this engine through a documented engine-specific contract before release.",
        )

    allowed = set(contract["allowed_top_level"])
    unexpected = sorted(set(snapshot) - allowed)
    if unexpected:
        add_finding(
            findings,
            "low",
            snapshot,
            "shape",
            f"Observed undocumented top-level block(s): {', '.join(unexpected)}.",
            "Decide whether the new block belongs in public docs, an engine-specific schema, or an ignored internal field.",
        )


def validate_status(snapshot: dict[str, Any], findings: list[Finding]) -> None:
    status = int(snapshot.get("http_status", 0))
    if status in {401, 403}:
        add_finding(
            findings,
            "blocker",
            snapshot,
            "access",
            f"Snapshot returned HTTP {status}; response quality cannot be trusted.",
            "Keep the last known-good response active, verify sanctioned access, and rerun before updating customer-facing output.",
        )
    elif status >= 500:
        add_finding(
            findings,
            "high",
            snapshot,
            "access",
            f"Snapshot returned HTTP {status}.",
            "Retry with backoff and record the incident in the customer support thread if the failure repeats.",
        )


def validate_organic_results(snapshot: dict[str, Any], contract: dict[str, Any], findings: list[Finding]) -> None:
    organic = snapshot.get("organic_results")
    if not isinstance(organic, list):
        return

    minimum = int(contract["minimum_organic_results"])
    if len(organic) < minimum:
        severity = "blocker" if not organic else "high"
        add_finding(
            findings,
            severity,
            snapshot,
            "coverage",
            f"Only {len(organic)} organic result(s) returned; contract expects at least {minimum}.",
            "Compare fixture HTML/API samples against the parser and keep this query in the regression suite.",
        )

    required_fields = set(contract["organic_required_fields"])
    empty_snippets = 0
    links: list[str] = []
    positions: list[int] = []
    for index, result in enumerate(organic, start=1):
        if not isinstance(result, dict):
            add_finding(
                findings,
                "high",
                snapshot,
                "shape",
                f"Organic result #{index} is not an object.",
                "Reject the result and add a serializer test for this engine.",
            )
            continue

        missing = sorted(required_fields - set(result))
        if missing:
            add_finding(
                findings,
                "high",
                snapshot,
                "shape",
                f"Organic result #{index} is missing field(s): {', '.join(missing)}.",
                "Patch extraction and add a fixture asserting all documented fields exist.",
            )

        link = result.get("link")
        if isinstance(link, str) and link:
            links.append(link)

        position = result.get("position")
        if isinstance(position, int):
            positions.append(position)
        else:
            add_finding(
                findings,
                "medium",
                snapshot,
                "ranking",
                f"Organic result #{index} has a non-integer position.",
                "Normalize ranking values before returning the response.",
            )

        snippet = result.get("snippet")
        if not isinstance(snippet, str) or not snippet.strip():
            empty_snippets += 1

    duplicate_links = len(links) - len(set(links))
    if duplicate_links > int(contract["max_duplicate_links"]):
        add_finding(
            findings,
            "high",
            snapshot,
            "dedupe",
            f"Found {duplicate_links} duplicate organic link(s).",
            "Dedupe by canonical URL before returning results and add duplicate-link fixtures.",
        )

    if positions and positions != list(range(1, len(positions) + 1)):
        add_finding(
            findings,
            "medium",
            snapshot,
            "ranking",
            f"Organic result positions are {positions}, not a contiguous 1..N sequence.",
            "Check whether ads, related blocks, or parser skips are leaking into organic ranking.",
        )

    if organic:
        empty_ratio = empty_snippets / len(organic)
        if empty_ratio > float(contract["max_empty_snippet_ratio"]):
            add_finding(
                findings,
                "medium",
                snapshot,
                "content",
                f"Empty snippet ratio is {empty_ratio:.0%}.",
                "Repair snippet extraction or document why this engine/query cannot provide snippets.",
            )


def review_snapshots(snapshots: list[dict[str, Any]], contract: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for snapshot in snapshots:
        validate_top_level(snapshot, contract, findings)
        validate_status(snapshot, findings)
        validate_organic_results(snapshot, contract, findings)
    return sorted(
        findings,
        key=lambda item: (
            SEVERITY_ORDER[item.severity],
            item.ticket_id,
            item.engine,
            item.area,
        ),
    )


def summarize(snapshots: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
    counts_by_severity = {severity: 0 for severity in SEVERITY_ORDER}
    counts_by_area: dict[str, int] = {}
    tickets_with_findings: set[str] = set()
    for finding in findings:
        counts_by_severity[finding.severity] += 1
        counts_by_area[finding.area] = counts_by_area.get(finding.area, 0) + 1
        tickets_with_findings.add(finding.ticket_id)

    decision = "release_candidate"
    if counts_by_severity["blocker"]:
        decision = "hold_release"
    elif counts_by_severity["high"]:
        decision = "repair_before_release"

    return {
        "decision": decision,
        "snapshots_reviewed": len(snapshots),
        "tickets_with_findings": sorted(tickets_with_findings),
        "counts_by_severity": counts_by_severity,
        "counts_by_area": counts_by_area,
    }


def write_outputs(findings: list[Finding], summary: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    findings_json = [asdict(finding) for finding in findings]
    (out_dir / "findings.json").write_text(json.dumps(findings_json, indent=2) + "\n")
    (out_dir / "monitor_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    with (out_dir / "findings.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(Finding.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(findings_json)

    top = findings[:5]
    lines = [
        "# Search Result Contract Monitor Handoff",
        "",
        f"Decision: `{summary['decision']}`",
        f"Snapshots reviewed: {summary['snapshots_reviewed']}",
        f"Tickets with findings: {', '.join(summary['tickets_with_findings']) or 'none'}",
        "",
        "## Top Findings",
    ]
    if not top:
        lines.append("- No findings. This response set is a release candidate.")
    for finding in top:
        lines.append(
            f"- `{finding.severity}` `{finding.ticket_id}` `{finding.engine}`: "
            f"{finding.problem} Recommendation: {finding.recommendation}"
        )
    lines.extend(
        [
            "",
            "## Customer-Support Note",
            "",
            "I reproduced the response-quality issue with a small contract check and separated release blockers from lower-risk documentation/schema notes. The current recommendation is to hold or repair only the affected engines, keep last known-good output active for impacted queries, and add the failing snapshots to the regression suite before release.",
        ]
    )
    (out_dir / "handoff_note.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Review fictional search API snapshots against a response contract.")
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    contract = load_contract(args.contract)
    snapshots = load_snapshots(args.snapshots)
    findings = review_snapshots(snapshots, contract)
    summary = summarize(snapshots, findings)
    write_outputs(findings, summary, args.out)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
