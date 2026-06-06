# Workflow Reliability Monitor

Public-safe operations demo for the part of automation work buyers often care about most: what happens when the workflow fails, retries, duplicates a write, or starts running slowly.

The demo uses fictional run logs and dry-run alert/retry payloads. In a client project, the same pattern can sit behind n8n execution logs, webhook callbacks, a database table, Slack/email alerts, or a lightweight dashboard.

## What It Produces

- `output/run_health.csv`: per-run severity, route, and recommended action.
- `output/retry_payloads.json`: dry-run retry requests with idempotency keys.
- `output/incident_digest.md`: owner-ready incident review and launch gates.
- `output/run_summary.json`: success rate, route counts, severity counts, and owner counts.

## Run

```bash
python3 workflow_reliability_monitor.py --input input/flow_runs.csv --out output
python3 -m pytest test_workflow_reliability_monitor.py
```

## Client Handoff Notes

Good first milestone:

- Define retryable vs non-retryable failures.
- Require idempotency keys on write paths.
- Create an owner route for incidents and expired credentials.
- Keep retry, alert, and pause actions in dry-run mode until sample logs pass.
- Deliver a short incident digest and runbook so the client can operate the workflow after handoff.
