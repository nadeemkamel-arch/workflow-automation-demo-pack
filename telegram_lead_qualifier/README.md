# Telegram Lead Qualifier

Public-safe MVP pattern for a Telegram intake bot that asks structured questions, stores lead data, prepares an AI summary, and alerts the owner only when the lead passes basic gates.

The demo uses fictional lead rows instead of a live Telegram bot token. In a client project, the same shape can sit behind a Telegram Bot API webhook in n8n, then write to Google Sheets or Supabase and call an approved LLM provider.

## What It Produces

- `output/lead_records.csv`: scored leads with referral source, priority, review route, and idempotency key.
- `output/ai_summary_payloads.json`: dry-run structured LLM payloads.
- `output/telegram_notifications.json`: dry-run owner alert payloads for hot leads.
- `output/mvp_acceptance_report.md`: milestone acceptance test and deferred scope.
- `output/run_summary.json`: counts, routes, and dry-run notification total.

## Run

```bash
python3 telegram_lead_qualifier.py --input input/lead_intake.csv --out output
python3 -m pytest test_telegram_lead_qualifier.py
```

## Client Handoff Notes

Good first milestone:

- 7-10 question Telegram intake.
- Source/referral tracking from the start link.
- Google Sheets or Supabase storage.
- Structured AI summary with an approved LLM provider.
- Owner notification for hot leads.
- Consent/off-scope routing before any follow-up.

Keep payment, CRM writeback, and automatic customer-facing follow-up as separate milestones unless credentials, acceptance tests, and refund/support rules are already defined.
