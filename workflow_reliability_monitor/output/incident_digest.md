# Workflow Reliability Incident Digest

Fictional sample output. Retry, alert, and pause actions are dry-run only.

| Run | Workflow | Severity | Route | Owner | Action | Error |
| --- | --- | --- | --- | --- | --- | --- |
| RUN-1001 | invoice_intake | warning | idempotency_review | finance_ops | verify_duplicate_was_deduped | - |
| RUN-1002 | invoice_intake | warning | idempotency_review | finance_ops | verify_duplicate_was_deduped | - |
| RUN-1003 | telegram_lead_alert | warning | retry_queue | sales_ops | schedule_retry_with_backoff | RATE_LIMIT |
| RUN-1004 | telegram_lead_alert | critical | incident_review | sales_ops | page_owner_and_pause_workflow | AUTH_EXPIRED |
| RUN-1005 | statement_email | notice | performance_review | finance_ops | inspect_slow_run | - |
| RUN-1006 | crm_sync | warning | retry_queue | rev_ops | schedule_retry_with_backoff | TIMEOUT |
| RUN-1007 | crm_sync | warning | idempotency_review | rev_ops | verify_duplicate_was_deduped | - |

## Launch Gate

- Confirm which failures are retryable before enabling automatic retry.
- Keep destructive or customer-facing actions behind a pause-and-review route.
- Require idempotency keys on every write path.
- Send owner alerts to Slack, email, or PagerDuty only after sample runs pass.
