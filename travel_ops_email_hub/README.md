# Travel Ops Email Hub

Public-safe travel-operations automation demo for Gmail-style inbox triage, Google Sheets status tracking, Slack urgent escalation, draft auto-replies, and staged booking-engine API payloads.

The demo uses fictional B2B travel-agency messages. It does not connect to Gmail, Google Sheets, Slack, or any booking engine. It shows the shape of a first paid pilot for operators who need sample-data-first email classification, loop protection, status tracking, urgent routing, idempotency keys, and review gates before live action.

## What It Produces

- `output/classification_queue.csv`: message-by-message category, priority, owner route, review reason, confidence, and idempotency key.
- `output/google_sheets_rows.json`: dry-run append/update rows for a travel operations sheet.
- `output/slack_alerts.json`: dry-run urgent Slack alerts for stranded/travel-risk messages.
- `output/draft_auto_replies.json`: Gmail-style draft replies for first-contact requests with loop-protection keys.
- `output/booking_api_payloads.json`: staged REST payloads for a fictional booking engine.
- `output/ops_digest.md`: manager-ready digest with launch gates.
- `output/run_summary.json`: route counts and proof that live action count is zero.

## Run

```bash
python3 travel_ops_email_hub.py --input input/travel_messages.csv --out output
python3 -m pytest test_travel_ops_email_hub.py
```

## Client Handoff Notes

Good first milestone:

- Start with 20-50 redacted travel-agency inbox messages.
- Confirm categories, status names, and owner routes before writing to live Sheets.
- Keep auto-replies in draft mode until duplicate and loop-protection checks pass.
- Keep urgent Slack alerts in dry-run until on-call ownership is approved.
- Treat booking-engine updates as staged payloads until REST docs, auth, rollback rules, and idempotency requirements are confirmed.
- Add connectors only after sample outputs match the operator's real workflow.
