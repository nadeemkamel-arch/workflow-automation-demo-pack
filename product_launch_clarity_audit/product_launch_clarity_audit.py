#!/usr/bin/env python3
"""Generate a small product-launch clarity audit from structured notes."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HIGH_RISK_TERMS = {
    "no source": "Trust gap",
    "source links": "Trust gap",
    "privacy": "Trust gap",
    "closed": "Trust gap",
    "does not name": "Message gap",
    "generic": "Message gap",
    "no example": "Proof gap",
}

MEDIUM_RISK_TERMS = {
    "twelve fields": "Effort gap",
    "vague": "Decision gap",
    "compete": "Focus gap",
    "hidden": "Control gap",
}


@dataclass(frozen=True)
class Issue:
    priority: int
    severity: str
    surface: str
    risk_type: str
    user_risk: str
    recommendation: str
    evidence: str
    effort: str


def load_product(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def classify_friction(text: str) -> tuple[str, str]:
    lowered = text.lower()
    for term, risk_type in HIGH_RISK_TERMS.items():
        if term in lowered:
            return "high", risk_type
    for term, risk_type in MEDIUM_RISK_TERMS.items():
        if term in lowered:
            return "medium", risk_type
    return "low", "Polish gap"


def recommendation_for(risk_type: str, surface: str, friction: str) -> tuple[str, str]:
    if risk_type == "Message gap":
        return (
            f"Rewrite {surface} around the concrete output the user gets first.",
            "small",
        )
    if risk_type == "Proof gap":
        return (
            f"Add one realistic example directly on {surface} before asking for signup.",
            "small",
        )
    if risk_type == "Trust gap":
        return (
            f"Make verification visible on {surface}: source links, privacy note, or date checks.",
            "medium",
        )
    if risk_type == "Effort gap":
        return (
            f"Reduce required inputs on {surface} or show a preview before the long form.",
            "medium",
        )
    if risk_type == "Focus gap":
        return (
            f"Choose one primary action on {surface} and make the other action visually secondary.",
            "small",
        )
    if risk_type == "Decision gap":
        return (
            f"Replace vague choices on {surface} with concrete examples or ranges.",
            "small",
        )
    if risk_type == "Control gap":
        return (
            f"Move edit controls higher on {surface} so users know the generated output is adjustable.",
            "medium",
        )
    return (f"Polish the confusing detail on {surface}: {friction}.", "small")


def build_issues(product: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    priority = 1
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    effort_rank = {"small": 0, "medium": 1, "large": 2}

    for screen in product["screens"]:
        surface = screen["name"]
        evidence = screen["evidence"]
        for friction in screen["friction_points"]:
            severity, risk_type = classify_friction(friction)
            recommendation, effort = recommendation_for(risk_type, surface, friction)
            issues.append(
                Issue(
                    priority=priority,
                    severity=severity,
                    surface=surface,
                    risk_type=risk_type,
                    user_risk=friction,
                    recommendation=recommendation,
                    evidence=evidence,
                    effort=effort,
                )
            )
            priority += 1

    issues.sort(key=lambda item: (severity_rank[item.severity], effort_rank[item.effort], item.priority))
    return [
        Issue(
            priority=index,
            severity=issue.severity,
            surface=issue.surface,
            risk_type=issue.risk_type,
            user_risk=issue.user_risk,
            recommendation=issue.recommendation,
            evidence=issue.evidence,
            effort=issue.effort,
        )
        for index, issue in enumerate(issues, start=1)
    ]


def readiness_score(product: dict[str, Any], issues: list[Issue]) -> int:
    score = 100
    score -= sum(5 for issue in issues if issue.severity == "high")
    score -= sum(3 for issue in issues if issue.severity == "medium")
    score -= sum(1 for issue in issues if issue.severity == "low")

    for check in product["readiness_checks"]:
        status = check["status"]
        if status == "missing":
            score -= 8
        elif status == "weak":
            score -= 4

    return max(0, min(100, score))


def launch_decision(score: int, issues: list[Issue]) -> str:
    high_count = sum(1 for issue in issues if issue.severity == "high")
    if high_count >= 3 or score < 55:
        return "not ready for broad launch; ready for a small private test after quick wins"
    if score < 75:
        return "ready for a small beta only"
    return "ready for a broader beta"


def write_issues_csv(path: Path, issues: list[Issue]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "priority",
                "severity",
                "surface",
                "risk_type",
                "user_risk",
                "recommendation",
                "evidence",
                "effort",
            ],
        )
        writer.writeheader()
        for issue in issues:
            writer.writerow(issue.__dict__)


def write_quick_wins(path: Path, product: dict[str, Any], issues: list[Issue]) -> None:
    top = issues[:3]
    lines = [
        f"# Quick Wins: {product['product_name']}",
        "",
        "Fix these before inviting a broader audience:",
        "",
    ]
    for issue in top:
        lines.append(f"{issue.priority}. **{issue.surface}** - {issue.recommendation}")
        lines.append(f"   - Why: {issue.user_risk}")
        lines.append(f"   - Effort: {issue.effort}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_message_tests(path: Path, product: dict[str, Any]) -> None:
    name = product["product_name"]
    audience = product["audience"]
    lines = [
        f"# Message Tests: {name}",
        "",
        "Three simple messages to test before posting publicly:",
        "",
        "## Option A: Concrete Output",
        f"Turn a few trip preferences into a one-page city itinerary you can edit before booking.",
        "",
        "## Option B: Time Saved",
        f"For {audience}, get a first trip plan in minutes instead of juggling tabs.",
        "",
        "## Option C: Trust First",
        "Build a starter itinerary with visible source links, date checks, and easy swaps.",
        "",
        "Suggested test: show each message to five target users and ask what they expect to see after clicking.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(path: Path, product: dict[str, Any], issues: list[Issue], score: int) -> None:
    decision = launch_decision(score, issues)
    high_count = sum(1 for issue in issues if issue.severity == "high")
    medium_count = sum(1 for issue in issues if issue.severity == "medium")

    lines = [
        f"# Product Launch Clarity Audit: {product['product_name']}",
        "",
        f"Category: {product['category']}",
        f"Stage: {product['stage']}",
        f"Audience: {product['audience']}",
        f"Business goal: {product['business_goal']}",
        "",
        f"Readiness score: {score}/100",
        f"Decision: {decision}.",
        "",
        "## What To Fix First",
        "",
    ]

    for issue in issues[:5]:
        lines.append(
            f"- **P{issue.priority} {issue.surface}:** {issue.recommendation} "
            f"({issue.severity}, {issue.risk_type})"
        )

    lines.extend(
        [
            "",
            "## Risk Summary",
            "",
            f"- High-risk clarity/trust gaps: {high_count}",
            f"- Medium-risk effort/control gaps: {medium_count}",
            "- Recommended next step: make the first three quick wins, then run a ten-person beta.",
            "",
            "## Scope Boundary",
            "",
            "This audit does not claim production UX research. It is a practical pre-launch review built from supplied notes, screenshots, or a public URL.",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(path: Path, product: dict[str, Any], issues: list[Issue], score: int) -> None:
    summary = {
        "product_name": product["product_name"],
        "issues_found": len(issues),
        "high_severity": sum(1 for issue in issues if issue.severity == "high"),
        "medium_severity": sum(1 for issue in issues if issue.severity == "medium"),
        "readiness_score": score,
        "decision": launch_decision(score, issues),
        "auto_changes_made": 0,
        "launch_gate": "owner_review_required_before_public_launch",
    }
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def run(input_path: Path, out_dir: Path) -> dict[str, Any]:
    product = load_product(input_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    issues = build_issues(product)
    score = readiness_score(product, issues)

    write_issues_csv(out_dir / "issue_queue.csv", issues)
    write_quick_wins(out_dir / "quick_wins.md", product, issues)
    write_message_tests(out_dir / "message_tests.md", product)
    write_report(out_dir / "readiness_report.md", product, issues, score)
    write_summary(out_dir / "run_summary.json", product, issues, score)

    return {
        "issues_found": len(issues),
        "high_severity": sum(1 for issue in issues if issue.severity == "high"),
        "medium_severity": sum(1 for issue in issues if issue.severity == "medium"),
        "readiness_score": score,
        "decision": launch_decision(score, issues),
        "auto_changes_made": 0,
        "launch_gate": "owner_review_required_before_public_launch",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    summary = run(args.input, args.out)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
