from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

REQUIRED_COLUMNS = {
    "id",
    "company",
    "channel",
    "request",
    "last_touch_days",
    "value_estimate",
    "deadline",
    "notes",
}

FIT_KEYWORDS = {
    "api": 12,
    "automate": 14,
    "automation": 14,
    "csv": 10,
    "draft": 8,
    "export": 8,
    "form": 6,
    "lead": 8,
    "pdf": 10,
    "report": 12,
    "script": 12,
    "spreadsheet": 10,
    "webhook": 12,
    "zapier": 12,
}

RISK_KEYWORDS = {
    "homework answers": "academic_cheating",
    "cheating": "academic_cheating",
    "fake review": "deceptive_promotion",
    "mass dm": "spam_or_bulk_outreach",
    "patient": "regulated_or_sensitive_data",
    "hipaa": "regulated_or_sensitive_data",
    "texts prospects": "automated_outreach_review",
    "sms": "automated_outreach_review",
}


@dataclass(frozen=True)
class TriageResult:
    id: str
    company: str
    channel: str
    request: str
    score: int
    priority: str
    risk_label: str
    recommended_action: str
    rationale: str


def _parse_int(value: str, *, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _days_until(raw_deadline: str, *, today: date | None = None) -> int | None:
    if not raw_deadline:
        return None
    today = today or date.today()
    try:
        return (date.fromisoformat(raw_deadline) - today).days
    except ValueError:
        return None


def _risk_for(text: str) -> str:
    lowered = text.lower()
    labels = [label for keyword, label in RISK_KEYWORDS.items() if keyword in lowered]
    if not labels:
        return "green"
    if "academic_cheating" in labels or "deceptive_promotion" in labels or "spam_or_bulk_outreach" in labels:
        return "red:" + ",".join(sorted(set(labels)))
    return "yellow:" + ",".join(sorted(set(labels)))


def score_row(row: dict[str, str], *, today: date | None = None) -> TriageResult:
    request = row.get("request", "").strip()
    notes = row.get("notes", "").strip()
    text = f"{request} {notes}".lower()
    risk_label = _risk_for(text)

    value = _parse_int(row.get("value_estimate", "0"))
    last_touch_days = _parse_int(row.get("last_touch_days", "0"))
    days_until = _days_until(row.get("deadline", ""), today=today)

    score = min(value // 50, 24)
    score += min(last_touch_days, 20)

    if days_until is not None:
        if days_until <= 1:
            score += 24
        elif days_until <= 3:
            score += 18
        elif days_until <= 7:
            score += 10

    matched_keywords: list[str] = []
    for keyword, weight in FIT_KEYWORDS.items():
        if keyword in text:
            score += weight
            matched_keywords.append(keyword)

    if risk_label.startswith("red"):
        score = 0
        priority = "do_not_pursue"
        recommended_action = "Decline. The request conflicts with service boundaries."
    elif risk_label.startswith("yellow"):
        score = min(score, 55)
        priority = "review_first"
        recommended_action = "Review policy and scope before proposing. Use sample data and keep human approval gates."
    elif score >= 70:
        priority = "high"
        recommended_action = "Prepare a scoped starter milestone and ask for sample data."
    elif score >= 45:
        priority = "medium"
        recommended_action = "Ask one clarifying question and offer a small workflow map."
    else:
        priority = "low"
        recommended_action = "Keep warm, but do not spend proposal time yet."

    rationale_parts = [
        f"value={value}",
        f"last_touch_days={last_touch_days}",
        f"deadline_delta={days_until if days_until is not None else 'unknown'}",
    ]
    if matched_keywords:
        rationale_parts.append("fit_keywords=" + ",".join(matched_keywords))
    if risk_label != "green":
        rationale_parts.append("risk=" + risk_label)

    return TriageResult(
        id=row.get("id", "").strip(),
        company=row.get("company", "").strip(),
        channel=row.get("channel", "").strip(),
        request=request,
        score=score,
        priority=priority,
        risk_label=risk_label,
        recommended_action=recommended_action,
        rationale="; ".join(rationale_parts),
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        return list(reader)


def triage(path: Path, *, today: date | None = None) -> list[TriageResult]:
    return [score_row(row, today=today) for row in read_rows(path)]


def write_outputs(results: list[TriageResult], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_results = sorted(results, key=lambda item: item.score, reverse=True)

    csv_path = out_dir / "triaged_inquiries.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(asdict(sorted_results[0]).keys()) if sorted_results else list(TriageResult.__dataclass_fields__)
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in sorted_results:
            writer.writerow(asdict(result))

    (out_dir / "action_plan.md").write_text(render_action_plan(sorted_results), encoding="utf-8")
    (out_dir / "follow_up_drafts.md").write_text(render_follow_up_drafts(sorted_results), encoding="utf-8")
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "total": len(sorted_results),
                "by_priority": _count_by(sorted_results, "priority"),
                "by_risk": _count_by(sorted_results, "risk_label"),
                "top_ids": [item.id for item in sorted_results[:3]],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _count_by(results: list[TriageResult], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        value = str(getattr(result, field_name))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def render_action_plan(results: list[TriageResult]) -> str:
    lines = [
        "# Action Plan",
        "",
        "Generated from a sample inbound queue. Review before using with real prospects.",
        "",
        "| Priority | Score | ID | Company | Action |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for item in results:
        lines.append(f"| {item.priority} | {item.score} | {item.id} | {item.company} | {item.recommended_action} |")

    lines.extend(["", "## Notes", ""])
    for item in results:
        lines.append(f"- {item.id}: {item.rationale}")
    lines.append("")
    return "\n".join(lines)


def render_follow_up_drafts(results: list[TriageResult]) -> str:
    lines = [
        "# Follow-Up Drafts",
        "",
        "These drafts are for human review. Do not send automatically.",
        "",
    ]
    for item in results:
        if item.priority == "do_not_pursue":
            lines.extend(
                [
                    f"## {item.id} - {item.company}",
                    "",
                    "No sales reply. Decline or ignore because the request conflicts with service boundaries.",
                    "",
                ]
            )
            continue

        opener = "I can help map this into a small first workflow." if item.priority != "review_first" else "I can take a cautious first look if we use sample data and keep review gates in place."
        lines.extend(
            [
                f"## {item.id} - {item.company}",
                "",
                f"Hi {item.company} team,",
                "",
                opener,
                "",
                f"My suggested first milestone would be: confirm the input, define the output, build a prototype, and deliver setup notes plus a validation checklist.",
                "",
                "Could you share a small sample file or a redacted example of the current workflow?",
                "",
                "Best,",
                "Nadeem",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Triage inbound automation requests into an action queue.")
    parser.add_argument("--input", required=True, type=Path, help="CSV input path")
    parser.add_argument("--out", required=True, type=Path, help="Output directory")
    args = parser.parse_args()

    results = triage(args.input)
    write_outputs(results, args.out)
    print(f"Wrote {len(results)} triaged rows to {args.out}")


if __name__ == "__main__":
    main()
