# Startup Finance Context Layer

Public-safe demo for an AI-powered accounting and finance services team.

The hard part in finance ops is not "ask an LLM a question." It is giving the operator a cited, permission-aware context packet from messy invoices, bank notes, payroll exports, Slack updates, and task history while keeping payment, reconciliation, and customer-facing actions behind explicit review gates.

This demo uses fictional startup finance records and deterministic retrieval. It produces context packets, dry-run task/accounting payloads, and a short digest that a finance operator could review before touching live systems.

## What It Produces

- `output/context_packets.json`: cited context packets for each finance request.
- `output/action_queue.csv`: dry-run task/accounting actions with owner approval required.
- `output/finance_ops_digest.md`: owner-readable request summary and launch gates.
- `output/run_summary.json`: route/action/source counts for handoff.

## Run

```bash
python3 finance_context_layer.py --records input/source_records.csv --requests input/operator_requests.csv --out output
python3 -m pytest test_finance_context_layer.py
```

## Boundaries

- Fictional sample data only.
- No live payments, accounting writes, customer replies, bank access, or credential handling.
- Retrieval is deterministic and inspectable; LLM usage would sit after the cited context packet, not before it.
- Actions are dry-run payloads until a human finance owner approves the source evidence and scope.

## Good First Paid Milestone

1. Import redacted exports or synthetic samples from approved finance tools.
2. Define source types, permissions, and no-write gates.
3. Build cited context packets for three recurring operator questions.
4. Emit dry-run task/accounting payloads.
5. Leave tests and a handoff note so the team can judge whether the context layer is trustworthy.
