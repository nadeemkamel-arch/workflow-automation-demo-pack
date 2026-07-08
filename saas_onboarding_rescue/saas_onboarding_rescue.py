#!/usr/bin/env python3
"""Build a dry-run SaaS onboarding rescue packet from trial-user data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class TrialUser:
    user_id: str
    name: str
    email: str
    company: str
    signup_days_ago: int
    first_project_created: bool
    invited_team: bool
    sent_first_message: bool
    last_seen_hours_ago: int
    plan_intent: str
    reply_signal: str
    blocker_note: str
    do_not_contact: bool


@dataclass(frozen=True)
class FollowUp:
    user: TrialUser
    risk_score: int
    segment: str
    email_key: str
    reason: str
    owner_action: str
    send_window_hours: int
    suppressed: bool = False


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def load_users(path: Path) -> list[TrialUser]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        return [
            TrialUser(
                user_id=row["user_id"],
                name=row["name"],
                email=row["email"],
                company=row["company"],
                signup_days_ago=int(row["signup_days_ago"]),
                first_project_created=parse_bool(row["first_project_created"]),
                invited_team=parse_bool(row["invited_team"]),
                sent_first_message=parse_bool(row["sent_first_message"]),
                last_seen_hours_ago=int(row["last_seen_hours_ago"]),
                plan_intent=row["plan_intent"],
                reply_signal=row["reply_signal"],
                blocker_note=row["blocker_note"],
                do_not_contact=parse_bool(row["do_not_contact"]),
            )
            for row in rows
        ]


def score_user(user: TrialUser, quiet_hours: int, stale_hours: int) -> int:
    score = 0
    if not user.first_project_created:
        score += 35
    if not user.sent_first_message:
        score += 20
    if user.last_seen_hours_ago >= quiet_hours:
        score += 15
    if user.last_seen_hours_ago >= stale_hours:
        score += 15
    if user.blocker_note:
        score += 10
    if user.reply_signal:
        score += 10
    if user.plan_intent == "high":
        score += 15
    elif user.plan_intent == "medium":
        score += 8
    if user.do_not_contact:
        score = 0
    return min(score, 100)


def choose_follow_up(user: TrialUser, rules: dict) -> FollowUp:
    quiet_hours = int(rules["quiet_hours"])
    stale_hours = int(rules["stale_hours"])

    if user.do_not_contact:
        return FollowUp(
            user=user,
            risk_score=0,
            segment="suppressed",
            email_key="suppress",
            reason="User is marked do-not-contact.",
            owner_action="Confirm consent status before any outreach.",
            send_window_hours=0,
            suppressed=True,
        )

    score = score_user(user, quiet_hours, stale_hours)

    if user.plan_intent == "high" and user.reply_signal:
        return FollowUp(
            user=user,
            risk_score=score,
            segment="high-intent",
            email_key="demo_invite",
            reason="High-intent user has already shown reply or demo signal.",
            owner_action="Offer a short guided walkthrough with one concrete agenda.",
            send_window_hours=12,
        )

    if not user.first_project_created and user.last_seen_hours_ago >= stale_hours:
        return FollowUp(
            user=user,
            risk_score=score,
            segment="cold-trial",
            email_key="last_chance_checkin",
            reason="Trial is stale before reaching the first valuable action.",
            owner_action="Send one useful final check-in, then stop unless they reply.",
            send_window_hours=12,
        )

    if not user.first_project_created:
        return FollowUp(
            user=user,
            risk_score=score,
            segment="setup-missing",
            email_key="setup_nudge",
            reason="User signed up but has not created the first project.",
            owner_action="Point to the first setup action and offer a tiny sample.",
            send_window_hours=24,
        )

    if user.blocker_note or (user.first_project_created and not user.sent_first_message):
        return FollowUp(
            user=user,
            risk_score=score,
            segment="blocked-after-start",
            email_key="human_unblocker",
            reason="User started setup but has not reached a first successful send.",
            owner_action="Ask one question and offer to unblock the exact next step.",
            send_window_hours=24,
        )

    return FollowUp(
        user=user,
        risk_score=score,
        segment="monitor",
        email_key="human_unblocker",
        reason="User is partly activated but still missing a clear next action.",
        owner_action="Review manually before adding more automation.",
        send_window_hours=48,
    )


def build_queue(users: Iterable[TrialUser], rules: dict) -> list[FollowUp]:
    queue = [choose_follow_up(user, rules) for user in users]
    return sorted(queue, key=lambda item: (item.suppressed, -item.risk_score, item.user.signup_days_ago))


def idempotency_key(user_id: str, email_key: str) -> str:
    digest = hashlib.sha256(f"{user_id}:{email_key}".encode("utf-8")).hexdigest()
    return f"dryrun_{digest[:16]}"


def write_queue(path: Path, queue: list[FollowUp]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "user_id",
                "company",
                "segment",
                "risk_score",
                "email_key",
                "reason",
                "owner_action",
                "send_window_hours",
                "suppressed",
            ],
        )
        writer.writeheader()
        for item in queue:
            writer.writerow(
                {
                    "user_id": item.user.user_id,
                    "company": item.user.company,
                    "segment": item.segment,
                    "risk_score": item.risk_score,
                    "email_key": item.email_key,
                    "reason": item.reason,
                    "owner_action": item.owner_action,
                    "send_window_hours": item.send_window_hours,
                    "suppressed": str(item.suppressed).lower(),
                }
            )


def write_payloads(path: Path, queue: list[FollowUp]) -> None:
    payloads = []
    for item in queue:
        if item.suppressed:
            continue
        payloads.append(
            {
                "idempotency_key": idempotency_key(item.user.user_id, item.email_key),
                "dry_run": True,
                "channel": "email",
                "to": item.user.email,
                "template": item.email_key,
                "crm_update": {
                    "user_id": item.user.user_id,
                    "segment": item.segment,
                    "risk_score": item.risk_score,
                    "next_owner_action": item.owner_action,
                },
                "headers": {"X-Dry-Run": "true"},
            }
        )
    path.write_text(json.dumps(payloads, indent=2) + "\n", encoding="utf-8")


def write_email_sequence(path: Path) -> None:
    path.write_text(
        """# 7-Day Plain-Text Email Sequence

All emails are drafts. The founder reviews copy, consent, unsubscribe handling, and live-send settings before launch.

## setup_nudge

Subject: Want me to set up the first project with you?

Hi {{first_name}},

I noticed you signed up but have not created the first project yet. The fastest path is usually:

1. add one source,
2. create one tiny example,
3. send one test result to yourself.

If you reply with what you are trying to set up, I can point you to the shortest first step.

## human_unblocker

Subject: Where did setup get stuck?

Hi {{first_name}},

It looks like you started but have not reached the first useful send yet. Quick question: is the blocker the data import, the message copy, or deciding what to send first?

Reply with one word and I will help you get unstuck.

## demo_invite

Subject: Want a quick walkthrough for {{company}}?

Hi {{first_name}},

Since you are already exploring this seriously, I can do a short walkthrough focused on one outcome: getting {{company}} from signup to first useful result.

If helpful, send me two times that work and I will keep it tight.

## last_chance_checkin

Subject: Should I close the loop here?

Hi {{first_name}},

I do not want to keep nudging if this is not useful. Before I close the loop, here is the shortest path I would try:

Create one small project with fake data, send one test message to yourself, and only then decide whether the workflow is worth expanding.

If you want help with that first pass, reply "setup" and I will send the steps.

## founder_review_note

Before sending anything live, review every recipient for consent, current relationship, unsubscribe requirements, and whether a human note would be more appropriate than automation.
""",
        encoding="utf-8",
    )


def write_checklist(path: Path, rules: dict, queue: list[FollowUp]) -> None:
    top = [item for item in queue if not item.suppressed][:3]
    lines = [
        "# Founder Sprint Checklist",
        "",
        f"Sprint length: {rules['sprint_days']} days",
        "",
        "## Day 0 Setup",
        "",
        "- Export trial users and key activation fields.",
        "- Mark do-not-contact and consent-sensitive records before scoring.",
        "- Define the first valuable action in one sentence.",
        "- Pick one email tool or CRM destination for dry-run payloads.",
        "",
        "## First Three Users To Review",
        "",
    ]
    for item in top:
        lines.append(
            f"- {item.user.company}: {item.segment}, {item.email_key}, score {item.risk_score}. {item.owner_action}"
        )
    lines.extend(
        [
            "",
            "## Launch Gate",
            "",
            "- Founder approves copy.",
            "- Unsubscribe and consent handling are confirmed.",
            "- First sends are manual or reviewed one by one.",
            "- Any automated follow-up starts in dry-run mode.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(path: Path, queue: list[FollowUp]) -> None:
    active = [item for item in queue if not item.suppressed]
    summary = {
        "users_scored": len(queue),
        "suppressed": len(queue) - len(active),
        "review_required": True,
        "top_segments": {},
        "live_actions": 0,
        "dry_run_payloads": len(active),
    }
    for item in active:
        summary["top_segments"][item.segment] = summary["top_segments"].get(item.segment, 0) + 1
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(users_path: Path, rules_path: Path, out_dir: Path) -> list[FollowUp]:
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    users = load_users(users_path)
    queue = build_queue(users, rules)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_queue(out_dir / "activation_queue.csv", queue)
    write_payloads(out_dir / "dry_run_payloads.json", queue)
    write_email_sequence(out_dir / "email_sequence.md")
    write_checklist(out_dir / "sprint_checklist.md", rules, queue)
    write_summary(out_dir / "run_summary.json", queue)
    return queue


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=Path, required=True)
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    queue = run(args.users, args.rules, args.out)
    print(f"Wrote onboarding rescue packet for {len(queue)} trial users to {args.out}")


if __name__ == "__main__":
    main()
