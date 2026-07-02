# Personal Risk Surface Audit

Public-safe demo for monitoring a person's exposed web risk without touching real private data.

Kanary-style work is not just scraping names from the web. The useful part is turning messy observations into a threat-model-aware review queue: what matters, why it matters, what should be checked by a human, and which actions must stay dry-run until approved.

This demo uses fictional observations and deterministic triage rules. In a real client workflow, inputs could come from approved exports, user-submitted links, internal analyst notes, or API data from permitted sources.

## What It Produces

- `output/remediation_queue.csv`: ranked findings with severity, route, and recommended next action.
- `output/review_packets.json`: dry-run analyst packets for human review.
- `output/audit_summary.md`: owner-readable digest and launch gates.
- `output/run_summary.json`: counts by severity, route, and source type.

## Run

```bash
python3 personal_risk_surface_audit.py --input input/observations.csv --out output
python3 -m pytest test_personal_risk_surface_audit.py
```

## Boundaries

- Fictional sample data only.
- No live outreach, takedowns, account changes, scraping, or credential handling.
- High-risk findings route to review packets instead of automated action.
- Removal or account-security steps require the user/account owner to approve and perform or authorize the next step.

## Good First Paid Milestone

A small paid milestone could be:

1. Define the threat model and excluded sources.
2. Import a redacted CSV of findings or analyst notes.
3. Rank findings into a review queue.
4. Produce dry-run remediation packets.
5. Leave a short handoff explaining what to verify manually.
