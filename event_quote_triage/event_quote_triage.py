from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_COLUMNS = {
    "id",
    "event_name",
    "event_date",
    "event_type",
    "wishlist_items",
    "guest_count",
    "city",
    "venue_address",
    "delivery_window",
    "setup_notes",
    "budget_notes",
}

CORE_FIELDS = {
    "event_date": "event date",
    "event_type": "event type",
    "wishlist_items": "wishlist items and quantities",
    "guest_count": "guest count",
    "city": "event city",
    "venue_address": "venue address",
    "delivery_window": "delivery/setup window",
}

LOCAL_CITIES = {"san diego", "la jolla", "del mar", "encinitas", "carlsbad", "solana beach"}


@dataclass(frozen=True)
class QuoteChecklist:
    id: str
    event_name: str
    readiness: str
    readiness_score: int
    missing_info: str
    delivery_flags: str
    staff_next_step: str
    draft_follow_up_questions: str


def _is_blank(value: str | None) -> bool:
    return not (value or "").strip() or (value or "").strip().lower() in {"tbd", "unknown", "n/a"}


def _missing_fields(row: dict[str, str]) -> list[str]:
    missing: list[str] = []
    for column, label in CORE_FIELDS.items():
        if _is_blank(row.get(column)):
            missing.append(label)
    return missing


def _delivery_flags(row: dict[str, str], missing: list[str]) -> list[str]:
    flags: list[str] = []
    city = (row.get("city") or "").strip().lower()
    setup_notes = (row.get("setup_notes") or "").strip().lower()

    if "delivery/setup window" in missing:
        flags.append("needs_delivery_window")
    if city and city not in LOCAL_CITIES:
        flags.append("check_service_area")
    if any(term in setup_notes for term in ("stairs", "elevator", "loading dock", "rooftop", "beach")):
        flags.append("review_access_or_setup_complexity")
    if _is_blank(row.get("venue_address")):
        flags.append("needs_exact_location")

    return flags or ["standard_review"]


def _readiness_score(missing: list[str], flags: list[str]) -> int:
    score = 100 - (len(missing) * 12)
    if "check_service_area" in flags:
        score -= 10
    if "review_access_or_setup_complexity" in flags:
        score -= 6
    return max(score, 0)


def _readiness_label(score: int) -> str:
    if score >= 85:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def _questions(row: dict[str, str], missing: list[str], flags: list[str]) -> list[str]:
    questions: list[str] = []
    for item in missing:
        if item == "wishlist items and quantities":
            questions.append("Which rental items and quantities should we quote?")
        elif item == "delivery/setup window":
            questions.append("What delivery and setup time window works for the event?")
        elif item == "venue address":
            questions.append("What is the exact venue or delivery address?")
        elif item == "guest count":
            questions.append("What guest count should we plan around?")
        else:
            questions.append(f"Can you confirm the {item}?")

    if "check_service_area" in flags:
        questions.append("Can you confirm whether the venue is inside the regular delivery area?")
    if "review_access_or_setup_complexity" in flags:
        questions.append("Are there access notes for stairs, elevators, loading, surface type, or setup restrictions?")
    if not questions:
        questions.append("Can you confirm the delivery address and preferred setup time before we finalize the quote?")

    return questions


def score_row(row: dict[str, str]) -> QuoteChecklist:
    missing = _missing_fields(row)
    flags = _delivery_flags(row, missing)
    score = _readiness_score(missing, flags)
    readiness = _readiness_label(score)
    questions = _questions(row, missing, flags)

    if readiness == "high":
        next_step = "Prepare quote draft after confirming address and setup timing."
    elif readiness == "medium":
        next_step = "Ask targeted follow-up questions before pricing."
    else:
        next_step = "Collect core event details before building a quote."

    return QuoteChecklist(
        id=(row.get("id") or "").strip(),
        event_name=(row.get("event_name") or "").strip(),
        readiness=readiness,
        readiness_score=score,
        missing_info=", ".join(missing) if missing else "none",
        delivery_flags=", ".join(flags),
        staff_next_step=next_step,
        draft_follow_up_questions=" | ".join(questions),
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        return list(reader)


def triage(path: Path) -> list[QuoteChecklist]:
    return [score_row(row) for row in read_rows(path)]


def render_staff_brief(results: list[QuoteChecklist]) -> str:
    sorted_results = sorted(results, key=lambda item: item.readiness_score, reverse=True)
    lines = [
        "# Event Quote Staff Brief",
        "",
        "Fictional sample output. Review before using with real customer data.",
        "",
        "| Readiness | Score | ID | Event | Missing Info | Next Step |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for item in sorted_results:
        lines.append(
            f"| {item.readiness} | {item.readiness_score} | {item.id} | {item.event_name} | "
            f"{item.missing_info} | {item.staff_next_step} |"
        )

    lines.extend(["", "## Follow-Up Questions", ""])
    for item in sorted_results:
        lines.append(f"### {item.id}: {item.event_name}")
        lines.append("")
        for question in item.draft_follow_up_questions.split(" | "):
            lines.append(f"- {question}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _count_by(results: list[QuoteChecklist], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        value = str(getattr(result, field_name))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def write_outputs(results: list[QuoteChecklist], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_results = sorted(results, key=lambda item: item.readiness_score, reverse=True)

    with (out_dir / "quote_checklist.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(QuoteChecklist.__dataclass_fields__)
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in sorted_results:
            writer.writerow(asdict(result))

    (out_dir / "staff_brief.md").write_text(render_staff_brief(sorted_results), encoding="utf-8")
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "total": len(sorted_results),
                "by_readiness": _count_by(sorted_results, "readiness"),
                "top_ready_ids": [item.id for item in sorted_results if item.readiness == "high"],
                "needs_follow_up_ids": [item.id for item in sorted_results if item.readiness != "high"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Turn event quote requests into staff-ready checklists.")
    parser.add_argument("--input", type=Path, required=True, help="CSV file of fictional event quote requests.")
    parser.add_argument("--out", type=Path, required=True, help="Directory for generated output files.")
    args = parser.parse_args()

    results = triage(args.input)
    write_outputs(results, args.out)
    print(f"Wrote {len(results)} event quote checklist rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
