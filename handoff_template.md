# Sandbox Workflow Handoff Checklist

Use this checklist for a small paid workflow pilot before any production credentials or private data are shared.

## Data Boundary

- First build uses fictional, redacted, or sandbox data.
- Production API keys, passwords, private customer records, payment data, and regulated data stay out of chat and out of the repo.
- Secrets belong in the client's credential store or approved secret manager, not in workflow JSON or scripts.

## Delivered Artifacts

- Exported workflow JSON or script files.
- Sample input payloads or CSVs.
- Expected output examples.
- Validation command or test checklist.
- Short runbook with setup, assumptions, edge cases, and maintenance notes.

## Acceptance Criteria

Define these before the build starts:

- Trigger: the exact event or file that starts the workflow.
- Input shape: required fields, optional fields, and sample values.
- Output target: file, JSON response, spreadsheet row, webhook, draft, report, or alert.
- Success case: one sample input produces the expected output.
- Failure case: missing, duplicate, malformed, or rejected input produces a logged review item instead of silent failure.

## Validation

For this public demo pack, validation runs locally:

```bash
python3 -m pytest n8n_ai_ops_triage/test_workflow_contract.py \
  ai_ops_triage/test_triage.py \
  event_quote_triage/test_event_quote_triage.py
```

A client pilot should include the same idea: one repeatable command or checklist that proves the agreed behavior against sample data.

## Handoff Notes

Each handoff should answer:

- What does the workflow do?
- What data does it read and write?
- Where do credentials live?
- What should happen when an API fails?
- Which outputs need human review before customer-facing action?
- What is intentionally out of scope for this milestone?

## Expansion Rule

Production deployment, live credentials, paid API usage, private data handling, and new integrations require a separate approved milestone.
