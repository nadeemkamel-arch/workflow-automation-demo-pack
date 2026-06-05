# Statement Email Preview

Fictional dry-run output. No email is sent.

| Type | Week | To | CC | Sessions | Minutes | Amount |
| --- | --- | --- | --- | ---: | ---: | ---: |
| external_recipient_weekly | 2026-06-01 | gomez@example.test | ops@example.test, billing@example.test | 1 | 60 | $240.00 |
| external_recipient_weekly | 2026-06-01 | lee@example.test | ops@example.test, billing@example.test | 2 | 60 | $225.00 |
| external_recipient_weekly | 2026-06-01 | patel@example.test | ops@example.test, billing@example.test | 1 | 30 | $120.00 |
| external_recipient_weekly | 2026-06-08 | lee@example.test | ops@example.test, billing@example.test | 1 | 50 | $200.00 |
| external_recipient_weekly | 2026-06-08 | patel@example.test | ops@example.test, billing@example.test | 1 | 20 | $60.00 |
| party_pair_weekly | 2026-06-01 | ops+north@example.test, billing+cedar@example.test | statements@example.test | 1 | 30 | $120.00 |
| party_pair_weekly | 2026-06-01 | ops+north@example.test, billing+river@example.test | statements@example.test | 2 | 60 | $225.00 |
| party_pair_weekly | 2026-06-01 | ops+south@example.test, billing+river@example.test | statements@example.test | 1 | 60 | $240.00 |
| party_pair_weekly | 2026-06-08 | ops+north@example.test, billing+river@example.test | statements@example.test | 1 | 50 | $200.00 |
| party_pair_weekly | 2026-06-08 | ops+south@example.test, billing+cedar@example.test | statements@example.test | 1 | 20 | $60.00 |

## Launch Gate

- Confirm SQL against the real PostgreSQL schema.
- Send to test recipients before enabling the schedule.
- Log each statement with an idempotency key before live send.
