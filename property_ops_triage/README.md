# Property Ops Triage

Public-safe property-management automation demo for inbox triage, maintenance routing, vendor invoice review, and dry-run owner handoff.

The demo uses fictional tenant/vendor messages and does not connect to Gmail, Slack, Asana, QuickBooks, AppFolio, Buildium, Rentvine, or any live account. It shows the shape of a first paid pilot for property-management operators: sample data first, deterministic routing, human review, idempotency keys, and no external sends.

## What It Produces

- `output/triage_queue.csv`: message-by-message category, priority, owner route, confidence, review reason, and idempotency key.
- `output/asana_task_payloads.json`: dry-run task payloads for maintenance/accounting/property-manager review.
- `output/invoice_review_packets.json`: vendor invoice packets with staged QuickBooks-style draft payloads.
- `output/slack_owner_digest.md`: owner-ready digest with launch gates.
- `output/run_summary.json`: route counts, priority counts, invoice packet count, and live-action count.

## Run

```bash
python3 property_ops_triage.py --input input/property_messages.csv --out output
python3 -m pytest test_property_ops_triage.py
```

## Client Handoff Notes

Good first milestone:

- Start with 20-50 redacted property-management inbox messages.
- Confirm categories and owner routes before live labels or task creation.
- Keep tenant/vendor replies in draft mode until manager approval.
- Require idempotency keys before creating Asana tasks, Slack alerts, or QuickBooks drafts.
- Treat duplicate invoice warnings as accounting-review-only until confirmed.
- Add system-specific connectors only after sample outputs match the operator's workflow.

