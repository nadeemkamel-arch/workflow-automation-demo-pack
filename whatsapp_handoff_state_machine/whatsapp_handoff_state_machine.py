#!/usr/bin/env python3
"""Build a public-safe WhatsApp/Gmail AI approval and human-handoff queue."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class MessageDecision:
    contact_id: str
    contact_name: str
    channel: str
    mode_before: str
    mode_after: str
    route: str
    urgency: str
    reason: str
    draft_reply: str
    approval_url: str
    next_human_action: str


def load_rules(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_messages(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def contains_any(text: str, keywords: Iterable[str]) -> list[str]:
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword.lower() in lowered]


def make_draft(message: dict[str, str], quote_match: bool) -> str:
    name = message["contact_name"]
    if quote_match:
        return (
            f"Hi {name}, thanks for the details. I can prepare this for review. "
            "Before anything is sent, please confirm quantity, delivery city, and any required deadline."
        )
    return (
        f"Hi {name}, thanks for reaching out. I drafted a response for review and will wait for approval "
        "before sending anything."
    )


def decide_message(message: dict[str, str], rules: dict) -> MessageDecision:
    text = message["message"]
    mode_before = message["current_mode"].strip().lower() or "ai"
    last_contact_hours = float(message["last_contact_hours_ago"] or 0)
    handoff_hits = contains_any(text, rules["human_handoff_keywords"])
    risk_hits = contains_any(text, rules["high_risk_keywords"])
    quote_hits = contains_any(text, rules["quote_keywords"])
    should_resume = mode_before == "human" and last_contact_hours >= float(rules["resume_after_hours"])

    contact_id = message["contact_id"]
    approval_url = f"{rules['approval_base_url'].rstrip('/')}/{contact_id}"

    if mode_before == "human" and not should_resume:
        return MessageDecision(
            contact_id=contact_id,
            contact_name=message["contact_name"],
            channel=message["channel"],
            mode_before=mode_before,
            mode_after="human",
            route="ai_paused",
            urgency="normal",
            reason="human_mode_active",
            draft_reply="",
            approval_url="",
            next_human_action="Secretary or owner continues the existing conversation.",
        )

    if handoff_hits or risk_hits:
        mode_after = "human"
        urgency = "high" if risk_hits else "normal"
        reason_parts = []
        if handoff_hits:
            reason_parts.append("handoff keywords: " + ", ".join(handoff_hits))
        if risk_hits:
            reason_parts.append("risk keywords: " + ", ".join(risk_hits))
        return MessageDecision(
            contact_id=contact_id,
            contact_name=message["contact_name"],
            channel=message["channel"],
            mode_before=mode_before,
            mode_after=mode_after,
            route="human_handoff",
            urgency=urgency,
            reason="; ".join(reason_parts),
            draft_reply="",
            approval_url="",
            next_human_action=(
                "Review conversation context, respond manually, and keep AI paused until the issue is resolved "
                f"or {rules['resume_after_hours']} hours pass without a new message."
            ),
        )

    return MessageDecision(
        contact_id=contact_id,
        contact_name=message["contact_name"],
        channel=message["channel"],
        mode_before=mode_before,
        mode_after="ai",
        route="draft_for_approval",
        urgency="normal",
        reason="resumed_after_idle" if should_resume else "safe_to_draft",
        draft_reply=make_draft(message, bool(quote_hits)),
        approval_url=approval_url,
        next_human_action="Review, edit if needed, then approve or reject. No auto-send occurs.",
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_handoff_markdown(path: Path, decisions: list[MessageDecision]) -> None:
    handoffs = [decision for decision in decisions if decision.route in {"human_handoff", "ai_paused"}]
    lines = ["# Human Handoff Packets", ""]
    if not handoffs:
        lines.append("No handoffs generated.")
    for decision in handoffs:
        lines.extend(
            [
                f"## {decision.contact_name} ({decision.contact_id})",
                "",
                f"- Channel: {decision.channel}",
                f"- Urgency: {decision.urgency}",
                f"- Mode before: {decision.mode_before}",
                f"- Mode after: {decision.mode_after}",
                f"- Reason: {decision.reason}",
                f"- Next action: {decision.next_human_action}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(messages_path: Path, rules_path: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    rules = load_rules(rules_path)
    messages = load_messages(messages_path)
    decisions = [decide_message(message, rules) for message in messages]
    decision_rows = [asdict(decision) for decision in decisions]

    approvals = [row for row in decision_rows if row["route"] == "draft_for_approval"]
    handoffs = [row for row in decision_rows if row["route"] in {"human_handoff", "ai_paused"}]
    state_rows = [
        {
            "contact_id": row["contact_id"],
            "contact_name": row["contact_name"],
            "channel": row["channel"],
            "mode": row["mode_after"],
            "last_route": row["route"],
            "urgency": row["urgency"],
        }
        for row in decision_rows
    ]

    write_csv(out_dir / "decision_log.csv", decision_rows)
    write_csv(out_dir / "approval_queue.csv", approvals)
    write_csv(out_dir / "state_table.csv", state_rows)
    write_handoff_markdown(out_dir / "handoff_packets.md", decisions)

    summary = {
        "business_name": rules["business_name"],
        "messages_processed": len(decisions),
        "drafts_waiting_for_approval": len(approvals),
        "human_handoffs": len([row for row in handoffs if row["route"] == "human_handoff"]),
        "ai_paused_threads": len([row for row in handoffs if row["route"] == "ai_paused"]),
        "auto_sends": 0,
        "launch_gate": "review_required_before_any_customer_message",
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--messages", type=Path, default=Path("input/messages.csv"))
    parser.add_argument("--rules", type=Path, default=Path("input/business_rules.json"))
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()
    summary = run(args.messages, args.rules, args.out)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
