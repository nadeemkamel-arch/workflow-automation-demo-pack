# Workflow Automation Demo Pack

Public-safe demos for scoped automation work: Python scripts, structured inputs, reproducible outputs, tests, and handoff notes.

These examples use fictional data and deterministic logic. In a client project, the same delivery shape can connect to approved tools such as Google Sheets exports, CRM CSVs, webhooks, REST APIs, or an n8n/Make/Zapier workflow. LLM calls can be added where they make sense, with clear data boundaries and cost approval.

## Demos

### AI Ops Triage

Path: `ai_ops_triage/`

Turns a messy inbound automation request queue into:

- a scored CSV,
- a manager-ready action plan,
- follow-up drafts for human review,
- a machine-readable JSON run summary.

Run:

```bash
cd ai_ops_triage
python3 triage.py --input input/inquiries.csv --out output
python3 -m pytest test_triage.py
```

### Event Quote Triage

Path: `event_quote_triage/`

Turns fictional event rental requests into:

- a staff-ready quote checklist CSV,
- missing-info prompts,
- a readable staff brief,
- a JSON run summary.

Run:

```bash
cd event_quote_triage
python3 event_quote_triage.py --input input/event_requests.csv --out output
python3 -m pytest test_event_quote_triage.py
```

## Good First Project

A good first milestone is narrow:

- one input source,
- one output format,
- sample or sandbox data,
- basic validation,
- setup notes,
- a review gate before customer-facing actions.

## Boundaries

These demos do not include production credentials, private client data, automatic outbound messages, regulated advice, spam tooling, fake engagement, or platform-rule bypassing.
