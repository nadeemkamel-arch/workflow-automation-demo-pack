# Statement Email Workflow

Public-safe demo for a database-backed weekly statement email workflow.

The fictional input represents session records already stored in a database. The script loads them into an in-memory SQLite database to demonstrate the same SQL grouping pattern a PostgreSQL-backed n8n workflow would need, then builds two statement types:

- paired weekly statements for two internal parties,
- external-recipient weekly statements with a different CC policy.

No email is sent. Outputs stay in dry-run mode.

## Outputs

- `output/statement_preview.md`: review table for all generated statement emails.
- `output/email_send_payloads.json`: staged mail-service `POST` payloads with idempotency keys.
- `output/dry_run_log.json`: no-send log for each statement.
- `output/run_summary.json`: counts by statement type and total amount represented.

## Run

```bash
python3 statement_email_workflow.py --input input/session_records.csv --out output
python3 -m pytest test_statement_email_workflow.py
```

## What This Proves

- SQL-backed grouping and summarization.
- Multi-recipient email statement generation.
- Separate routing rules for internal pair statements and external recipient statements.
- Dry-run payload review before any third-party mail provider is connected.
- Idempotency keys and launch gates for scheduled automation.

## Boundaries

This demo does not connect to a production database, send email, store credentials, process real financial records, or approve any statement. A real project should start with redacted schema details, test recipients, and one validated weekly workflow before enabling schedules.
