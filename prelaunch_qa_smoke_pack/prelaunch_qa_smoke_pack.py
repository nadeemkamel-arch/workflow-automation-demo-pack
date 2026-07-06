#!/usr/bin/env python3
"""Turn a small app-test cycle into QA outputs a founder can act on.

This is a public-safe proof artifact. It uses fictional test sessions and
generates bug reports, UX feedback, a retest checklist, and a release gate.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SEVERITY_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}

BLOCKER_TERMS = {
    "blank white screen",
    "cannot finish",
    "never opens",
    "crashed",
    "crash",
    "data loss",
    "fatal",
}

HIGH_TERMS = {
    "resets",
    "wrong reminder",
    "accessibility",
    "clipped",
    "cannot tell",
    "trust gap",
    "poor signal",
}

MEDIUM_TERMS = {
    "hidden",
    "overlaps",
    "confusing",
    "unfinished",
    "confirmation",
    "does not name",
}


@dataclass(frozen=True)
class Finding:
    priority: int
    severity: str
    category: str
    screen: str
    platform: str
    device: str
    action: str
    expected: str
    actual: str
    user_impact: str
    recommendation: str
    repro_steps: str
    evidence: str


def load_plan(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_sessions(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def row_text(row: dict[str, str]) -> str:
    return " ".join(row.get(field, "") for field in ("screen", "action", "actual", "user_impact")).lower()


def categorize(row: dict[str, str]) -> str:
    text = row_text(row)
    if any(term in text for term in ("signup", "account", "login")):
        return "account access"
    if any(term in text for term in ("blank", "crash", "offline", "poor signal", "airplane")):
        return "stability"
    if any(term in text for term in ("resets", "wrong reminder", "persist", "data loss")):
        return "data integrity"
    if any(term in text for term in ("accessibility", "font", "clipped", "contrast")):
        return "accessibility"
    if any(term in text for term in ("hidden", "confusing", "copy", "trust", "confirmation")):
        return "ux clarity"
    if any(term in text for term in ("overlap", "wrap", "visual", "unfinished")):
        return "visual polish"
    return "general qa"


def severity_for(row: dict[str, str]) -> str:
    if row.get("status", "").lower() == "pass":
        return "pass"

    text = row_text(row)
    if any(term in text for term in BLOCKER_TERMS):
        return "blocker"
    if any(term in text for term in HIGH_TERMS):
        return "high"
    if any(term in text for term in MEDIUM_TERMS):
        return "medium"
    return "low"


def recommendation_for(category: str, row: dict[str, str]) -> str:
    screen = row["screen"]
    if category == "account access":
        return f"Instrument and fix the {screen} continuation path, then retest signup on iOS Safari."
    if category == "stability":
        return f"Add an offline/error state for {screen} and capture client logs before beta invites."
    if category == "data integrity":
        return f"Preserve the selected schedule state on {screen} and add a regression check for saved values."
    if category == "accessibility":
        return f"Retest {screen} with large-font settings and keep tap targets visible at mobile widths."
    if category == "ux clarity":
        return f"Make the result of the action obvious on {screen}: confirmation, plain copy, or visible undo."
    if category == "visual polish":
        return f"Constrain long text on {screen} so content wraps without covering counters or controls."
    return f"Reproduce and fix the reported issue on {screen}, then retest the same device and platform."


def build_findings(sessions: list[dict[str, str]]) -> list[Finding]:
    findings: list[Finding] = []
    for row in sessions:
        severity = severity_for(row)
        if severity == "pass":
            continue

        category = categorize(row)
        findings.append(
            Finding(
                priority=0,
                severity=severity,
                category=category,
                screen=row["screen"],
                platform=row["platform"],
                device=row["device"],
                action=row["action"],
                expected=row["expected"],
                actual=row["actual"],
                user_impact=row["user_impact"],
                recommendation=recommendation_for(category, row),
                repro_steps=row["repro_steps"],
                evidence=row["evidence"],
            )
        )

    findings.sort(key=lambda item: (SEVERITY_ORDER[item.severity], item.category, item.screen))
    return [
        Finding(
            priority=index,
            severity=finding.severity,
            category=finding.category,
            screen=finding.screen,
            platform=finding.platform,
            device=finding.device,
            action=finding.action,
            expected=finding.expected,
            actual=finding.actual,
            user_impact=finding.user_impact,
            recommendation=finding.recommendation,
            repro_steps=finding.repro_steps,
            evidence=finding.evidence,
        )
        for index, finding in enumerate(findings, start=1)
    ]


def coverage_gaps(plan: dict[str, Any], sessions: list[dict[str, str]]) -> list[str]:
    covered = {row["screen"].strip().lower() for row in sessions}
    return [
        item
        for item in plan.get("minimum_coverage", [])
        if item.strip().lower() not in covered
    ]


def platform_gaps(plan: dict[str, Any], sessions: list[dict[str, str]]) -> list[str]:
    covered = {row["platform"].strip().lower() for row in sessions}
    required = plan.get("launch_rules", {}).get("required_platforms", [])
    return [item for item in required if item.strip().lower() not in covered]


def readiness_score(findings: list[Finding], gaps: list[str], missing_platforms: list[str]) -> int:
    score = 100
    score -= sum(20 for finding in findings if finding.severity == "blocker")
    score -= sum(10 for finding in findings if finding.severity == "high")
    score -= sum(5 for finding in findings if finding.severity == "medium")
    score -= sum(2 for finding in findings if finding.severity == "low")
    score -= len(gaps) * 6
    score -= len(missing_platforms) * 8
    return max(0, min(100, score))


def release_decision(plan: dict[str, Any], findings: list[Finding], gaps: list[str], missing_platforms: list[str]) -> str:
    rules = plan.get("launch_rules", {})
    blocker_count = sum(1 for finding in findings if finding.severity == "blocker")
    high_count = sum(1 for finding in findings if finding.severity == "high")

    if blocker_count > rules.get("blocker_max", 0):
        return "not ready for beta; fix blocker paths and retest before inviting users"
    if high_count > rules.get("high_max", 2):
        return "not ready for broad beta; reduce high-risk findings first"
    if gaps or missing_platforms:
        return "private test only; fill coverage gaps before a wider beta"
    return "ready for a limited beta after owner review"


def write_bug_report(path: Path, findings: list[Finding]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(findings[0]).keys()) if findings else ["priority"])
        writer.writeheader()
        for finding in findings:
            writer.writerow(asdict(finding))


def write_ux_feedback(path: Path, plan: dict[str, Any], findings: list[Finding]) -> None:
    ux_findings = [
        finding
        for finding in findings
        if finding.category in {"ux clarity", "accessibility", "visual polish"}
    ]
    lines = [
        f"# UX Feedback: {plan['product_name']}",
        "",
        f"Build reviewed: {plan['build']}",
        f"Release goal: {plan['release_goal']}",
        "",
        "## Highest Leverage Feedback",
        "",
    ]
    for finding in ux_findings[:5]:
        lines.append(
            f"- **P{finding.priority} {finding.screen} ({finding.severity}):** "
            f"{finding.recommendation}"
        )
        lines.append(f"  - User impact: {finding.user_impact}")

    if not ux_findings:
        lines.append("- No UX-specific findings were separated from the bug report.")

    lines.extend(
        [
            "",
            "## Product Note",
            "",
            "The app has enough useful paths to keep testing, but the first beta invite should wait until account access, offline behavior, and visible confirmations feel dependable.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_retest_checklist(path: Path, findings: list[Finding], gaps: list[str], missing_platforms: list[str]) -> None:
    lines = [
        "# Retest Checklist",
        "",
        "Run these checks after fixes land:",
        "",
    ]
    for finding in findings:
        lines.append(f"- [ ] P{finding.priority} {finding.screen} on {finding.platform}: {finding.action}")
        lines.append(f"  - Confirm: {finding.expected}")

    if gaps:
        lines.extend(["", "## Coverage Gaps", ""])
        lines.extend(f"- [ ] Add coverage for {gap}" for gap in gaps)

    if missing_platforms:
        lines.extend(["", "## Platform Gaps", ""])
        lines.extend(f"- [ ] Add at least one smoke test on {platform}" for platform in missing_platforms)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def summary_counts(findings: list[Finding]) -> dict[str, int]:
    return {
        severity: sum(1 for finding in findings if finding.severity == severity)
        for severity in SEVERITY_ORDER
    }


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def run(sessions_path: Path, plan_path: Path, out_dir: Path) -> dict[str, Any]:
    plan = load_plan(plan_path)
    sessions = load_sessions(sessions_path)
    findings = build_findings(sessions)
    gaps = coverage_gaps(plan, sessions)
    missing_platforms = platform_gaps(plan, sessions)
    score = readiness_score(findings, gaps, missing_platforms)
    decision = release_decision(plan, findings, gaps, missing_platforms)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_bug_report(out_dir / "bug_report.csv", findings)
    write_ux_feedback(out_dir / "ux_feedback.md", plan, findings)
    write_retest_checklist(out_dir / "retest_checklist.md", findings, gaps, missing_platforms)

    summary = {
        "product_name": plan["product_name"],
        "build": plan["build"],
        "sessions_reviewed": len(sessions),
        "findings_found": len(findings),
        "severity_counts": summary_counts(findings),
        "coverage_gaps": gaps,
        "missing_platforms": missing_platforms,
        "readiness_score": score,
        "release_decision": decision,
        "auto_changes_made": 0,
        "launch_gate": "owner_review_required_before_beta_invites",
    }
    write_summary(out_dir / "test_cycle_summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a prelaunch QA smoke-test pack.")
    parser.add_argument("--sessions", type=Path, required=True, help="CSV of fictional test sessions.")
    parser.add_argument("--plan", type=Path, required=True, help="JSON test plan and launch rules.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run(args.sessions, args.plan, args.out)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
