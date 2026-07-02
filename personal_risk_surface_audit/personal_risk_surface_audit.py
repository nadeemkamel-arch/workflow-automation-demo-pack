from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_COLUMNS = {
    "observation_id",
    "source_type",
    "source_name",
    "url",
    "person_signal",
    "finding",
    "evidence_type",
    "exposure",
    "sensitivity",
    "confidence",
    "first_seen",
    "owner_action",
}

SENSITIVITY_SCORE = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

EXPOSURE_SCORE = {
    "private_note": 0,
    "limited": 1,
    "public": 2,
}


@dataclass(frozen=True)
class RiskFinding:
    observation_id: str
    source_type: str
    source_name: str
    url: str
    person_signal: str
    finding: str
    evidence_type: str
    exposure: str
    sensitivity: str
    confidence: float
    first_seen: str
    owner_action: str
    score: int
    severity: str
    route: str
    next_action: str
    live_action_allowed: bool


def read_observations(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        rows = list(reader)
    if not rows:
        raise ValueError(f"No observations found in {path}")
    return rows


def _score(row: dict[str, str]) -> int:
    sensitivity = SENSITIVITY_SCORE.get(row["sensitivity"], 1)
    exposure = EXPOSURE_SCORE.get(row["exposure"], 0)
    confidence = float(row["confidence"])
    confidence_bonus = 2 if confidence >= 0.85 else 1 if confidence >= 0.65 else 0
    evidence_bonus = 2 if row["evidence_type"] in {"credential_signal", "impersonation_signal"} else 0
    return sensitivity * 2 + exposure + confidence_bonus + evidence_bonus


def _classify(row: dict[str, str]) -> tuple[str, str, str, bool]:
    evidence_type = row["evidence_type"]
    sensitivity = row["sensitivity"]
    owner_action = row["owner_action"]
    score = _score(row)

    if evidence_type == "credential_signal" or sensitivity == "critical":
        return "critical", "account_security_review", "verify_and_rotate_secret_with_owner", False
    if evidence_type == "impersonation_signal":
        return "high", "impersonation_review", "confirm_account_ownership_before_report", False
    if owner_action == "request_removal" or row["source_type"] == "data_broker":
        return "high", "removal_request_review", "prepare_data_broker_removal_packet", False
    if evidence_type == "stale_profile" or score >= 6:
        return "medium", "profile_cleanup_review", "prepare_profile_update_checklist", False
    return "low", "monitor", "keep_for_periodic_review", False


def analyze_observations(path: Path) -> list[RiskFinding]:
    findings: list[RiskFinding] = []
    for row in read_observations(path):
        score = _score(row)
        severity, route, next_action, live_action_allowed = _classify(row)
        findings.append(
            RiskFinding(
                observation_id=row["observation_id"],
                source_type=row["source_type"],
                source_name=row["source_name"],
                url=row["url"],
                person_signal=row["person_signal"],
                finding=row["finding"],
                evidence_type=row["evidence_type"],
                exposure=row["exposure"],
                sensitivity=row["sensitivity"],
                confidence=float(row["confidence"]),
                first_seen=row["first_seen"],
                owner_action=row["owner_action"],
                score=score,
                severity=severity,
                route=route,
                next_action=next_action,
                live_action_allowed=live_action_allowed,
            )
        )
    return sorted(findings, key=lambda finding: (-finding.score, finding.observation_id))


def build_review_packets(findings: list[RiskFinding]) -> list[dict[str, object]]:
    packets = []
    for finding in findings:
        if finding.route == "monitor":
            continue
        packets.append(
            {
                "packet_id": f"review:{finding.observation_id}",
                "status": "dry_run_only",
                "route": finding.route,
                "severity": finding.severity,
                "source": {
                    "type": finding.source_type,
                    "name": finding.source_name,
                    "url": finding.url,
                },
                "evidence": {
                    "signal": finding.person_signal,
                    "type": finding.evidence_type,
                    "finding": finding.finding,
                    "confidence": finding.confidence,
                },
                "recommended_next_action": finding.next_action,
                "requires_owner_approval": True,
            }
        )
    return packets


def _count(findings: list[RiskFinding], field_name: str) -> dict[str, int]:
    return dict(Counter(str(getattr(finding, field_name)) for finding in findings))


def render_summary(findings: list[RiskFinding]) -> str:
    lines = [
        "# Personal Risk Surface Audit Summary",
        "",
        "Fictional sample output. No live outreach, takedown, scraping, or account action was performed.",
        "",
        "| ID | Severity | Route | Source | Signal | Next Action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for finding in findings:
        lines.append(
            " | ".join(
                [
                    f"| {finding.observation_id}",
                    finding.severity,
                    finding.route,
                    finding.source_name,
                    finding.person_signal,
                    finding.next_action + " |",
                ]
            )
        )
    lines.extend(
        [
            "",
            "## Launch Gate",
            "",
            "- Confirm each match with the account owner before remediation.",
            "- Keep removal, reporting, password reset, and account-security actions manual until approved.",
            "- Treat token-shaped strings as sensitive even when they may be false positives.",
            "- Store real evidence in the client's approved private system, not in a public repo.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(findings: list[RiskFinding], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_findings = sorted(findings, key=lambda finding: (-finding.score, finding.observation_id))
    fieldnames = list(asdict(sorted_findings[0]).keys())

    with (out_dir / "remediation_queue.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(asdict(finding) for finding in sorted_findings)

    review_packets = build_review_packets(sorted_findings)
    (out_dir / "review_packets.json").write_text(
        json.dumps(review_packets, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "audit_summary.md").write_text(render_summary(sorted_findings), encoding="utf-8")
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "finding_count": len(sorted_findings),
                "review_packet_count": len(review_packets),
                "severity_counts": _count(sorted_findings, "severity"),
                "route_counts": _count(sorted_findings, "route"),
                "source_type_counts": _count(sorted_findings, "source_type"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a dry-run personal risk surface audit.")
    parser.add_argument("--input", type=Path, default=Path("input/observations.csv"))
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()

    findings = analyze_observations(args.input)
    write_outputs(findings, args.out)


if __name__ == "__main__":
    main()
