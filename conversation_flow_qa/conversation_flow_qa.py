from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_COLUMNS = {
    "id",
    "campaign",
    "message",
    "customer_status",
    "last_appointment_days",
}

CAMPAIGN_GOALS = {
    "post_visit": "Protect client trust after a recent service.",
    "rebooking": "Help the client choose a new appointment time.",
    "vip_retention": "Answer loyalty questions and keep the client experience high-touch.",
    "winback": "Invite a lapsed client back without pressure.",
}

RISK_KEYWORDS = {
    "opt_out": {"stop", "unsubscribe", "do not text", "dont text", "don't text", "remove me"},
    "complaint": {"unhappy", "badly", "nobody followed up", "angry", "refund", "complaint"},
    "medical_or_reaction": {"reacted", "redness", "burning", "swelling", "rash", "infection"},
    "pricing_exception": {"match my old price", "discount", "free", "package credit", "refund"},
    "late_arrival": {"late", "running behind", "still ok"},
    "competitor_booked": {"booked somewhere else", "another spa", "different salon"},
}


@dataclass(frozen=True)
class ConversationCheck:
    id: str
    campaign: str
    intent: str
    risk_flags: str
    route: str
    quality_checks: str
    draft_response_rule: str


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _risk_flags(message: str) -> list[str]:
    normalized = _normalize(message)
    flags: list[str] = []
    for flag, keywords in RISK_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            flags.append(flag)
    return flags or ["standard"]


def _intent(message: str, flags: list[str]) -> str:
    normalized = _normalize(message)
    if "opt_out" in flags:
        return "opt_out"
    if "complaint" in flags or "medical_or_reaction" in flags:
        return "service_recovery"
    if "late_arrival" in flags:
        return "same_day_schedule_issue"
    if "pricing_exception" in flags:
        return "policy_or_pricing_question"
    if "competitor_booked" in flags:
        return "not_ready"
    if any(term in normalized for term in ("book", "same time", "next friday", "move", "reschedule")):
        return "schedule_request"
    if any(term in normalized for term in ("how much", "price", "cost")):
        return "pricing_question"
    if any(term in normalized for term in ("address", "where are you", "location")):
        return "logistics_question"
    return "unclear_interest"


def _route(intent: str, flags: list[str]) -> str:
    if "opt_out" in flags:
        return "suppress_and_confirm"
    if "complaint" in flags or "medical_or_reaction" in flags:
        return "human_owner_review"
    if intent == "same_day_schedule_issue":
        return "front_desk_review"
    if "pricing_exception" in flags:
        return "manager_policy_review"
    if intent in {"schedule_request", "pricing_question", "logistics_question", "unclear_interest"}:
        return "ai_draft_then_human_review"
    return "no_push_follow_up"


def _quality_checks(intent: str, flags: list[str]) -> list[str]:
    checks = [
        "warm_brand_voice",
        "one_clear_next_step",
        "no_unapproved_discount",
    ]
    if "opt_out" in flags:
        checks = ["confirm_opt_out", "no_marketing_language", "suppress_future_campaigns"]
    elif "complaint" in flags or "medical_or_reaction" in flags:
        checks = ["acknowledge_without_defensiveness", "avoid_medical_advice", "owner_review_before_send"]
    elif intent == "schedule_request":
        checks.append("ask_for_two_time_options")
    elif intent == "pricing_question":
        checks.append("quote_from_approved_menu_only")
    elif intent == "unclear_interest":
        checks.append("ask_one_low_pressure_question")
    return checks


def _response_rule(intent: str, route: str) -> str:
    rules = {
        "opt_out": "Send a short opt-out confirmation and stop all campaign messages.",
        "service_recovery": "Draft an apology and hand to the owner before any customer reply.",
        "same_day_schedule_issue": "Route to front desk because timing affects the live calendar.",
        "policy_or_pricing_question": "State that a team member will confirm policy before promising a discount or credit.",
        "schedule_request": "Offer to check availability and ask for two preferred windows.",
        "pricing_question": "Answer only from the approved service menu and invite the client to choose an add-on.",
        "logistics_question": "Provide the approved location detail and ask whether they need parking notes.",
        "not_ready": "Acknowledge the choice and avoid pressure or repeated winback messages.",
        "unclear_interest": "Ask one simple question to clarify interest.",
    }
    if route in {"human_owner_review", "manager_policy_review", "front_desk_review"}:
        return rules[intent] + " Human review is required before send."
    return rules[intent]


def check_row(row: dict[str, str]) -> ConversationCheck:
    flags = _risk_flags(row.get("message", ""))
    intent = _intent(row.get("message", ""), flags)
    route = _route(intent, flags)
    return ConversationCheck(
        id=(row.get("id") or "").strip(),
        campaign=(row.get("campaign") or "").strip(),
        intent=intent,
        risk_flags=", ".join(flags),
        route=route,
        quality_checks=", ".join(_quality_checks(intent, flags)),
        draft_response_rule=_response_rule(intent, route),
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        return list(reader)


def analyze(path: Path) -> list[ConversationCheck]:
    return [check_row(row) for row in read_rows(path)]


def _count_by(results: list[ConversationCheck], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        value = str(getattr(result, field_name))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def render_test_matrix(results: list[ConversationCheck]) -> str:
    lines = [
        "# Conversation Flow QA Test Matrix",
        "",
        "Fictional sample output for reviewing AI conversation rules before any SMS send.",
        "",
        "| ID | Campaign Goal | Intent | Risk Flags | Route | Response Rule |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in results:
        goal = CAMPAIGN_GOALS.get(item.campaign, "Review campaign goal before launch.")
        lines.append(
            f"| {item.id} | {goal} | {item.intent} | {item.risk_flags} | "
            f"{item.route} | {item.draft_response_rule} |"
        )

    lines.extend(["", "## Launch Gate", ""])
    lines.append("- Confirm opt-out handling with the SMS platform before launch.")
    lines.append("- Keep complaints, skin reactions, policy exceptions, and same-day timing with staff.")
    lines.append("- Test each campaign with approved menu, pricing, location, and booking-policy text.")
    return "\n".join(lines).strip() + "\n"


def write_outputs(results: list[ConversationCheck], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_results = sorted(results, key=lambda item: (item.route, item.id))

    with (out_dir / "conversation_checks.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(ConversationCheck.__dataclass_fields__)
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in sorted_results:
            writer.writerow(asdict(result))

    (out_dir / "test_matrix.md").write_text(render_test_matrix(sorted_results), encoding="utf-8")
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "total": len(sorted_results),
                "by_route": _count_by(sorted_results, "route"),
                "by_intent": _count_by(sorted_results, "intent"),
                "human_review_ids": [
                    item.id
                    for item in sorted_results
                    if item.route in {"human_owner_review", "manager_policy_review", "front_desk_review"}
                ],
                "suppressed_ids": [
                    item.id for item in sorted_results if item.route == "suppress_and_confirm"
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a conversation-flow QA matrix for fictional customer messages."
    )
    parser.add_argument("--input", type=Path, required=True, help="CSV file of fictional customer messages.")
    parser.add_argument("--out", type=Path, required=True, help="Directory for generated output files.")
    args = parser.parse_args()

    results = analyze(args.input)
    write_outputs(results, args.out)
    print(f"Wrote {len(results)} conversation QA rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
