# Telegram Lead Qualifier MVP Acceptance Report

Fictional sample output. Telegram, LLM, payment, and CRM calls are staged only.

| Lead | Source | Contact | Score | Priority | Route |
| --- | --- | --- | ---: | --- | --- |
| TL-1001 | ref-austin-condo | @maya_test | 100 | hot | telegram_owner_alert |
| TL-1002 | ref-family-home | @omar_test | 57 | warm | weekly_lead_digest |
| TL-1003 | ref-passport-bot | @leah_test | 0 | review | consent_review_queue |
| TL-1004 | ref-investor-rus | @nadia_test | 93 | hot | telegram_owner_alert |

## First Milestone Acceptance Test

- User completes a 7-10 question Telegram intake.
- Source/referral code is saved with the lead record.
- Answers are stored in Google Sheets or Supabase-shaped rows.
- Structured AI summary payload is prepared for approved LLM provider.
- Hot leads create a dry-run owner notification payload.
- Non-consenting or off-scope leads route to review instead of outreach.

## Deferred Until Milestone Two

- Payment collection.
- CRM writeback.
- Production Telegram bot token.
- Automatic customer-facing follow-up.
