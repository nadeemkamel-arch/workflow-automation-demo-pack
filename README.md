# Agentic Workflow Automation Demo Pack

Public-safe demos for scoped automation work: n8n workflow JSON, Python scripts, API handoff payloads, document-processing flows, reproducible outputs, tests, and handoff notes.

These examples use fictional data so the code, outputs, and runbooks can be inspected publicly. The same delivery shape can connect to approved client systems such as Google Sheets exports, CRM CSVs, webhooks, REST APIs, LLM calls, or n8n/Make/Zapier workflows once the data source, credentials, cost controls, and launch gate are agreed.

Portfolio page:

https://nadeemkamel-arch.github.io/workflow-automation-demo-pack/

Pilot inquiry form:

https://github.com/nadeemkamel-arch/workflow-automation-demo-pack/issues/new?template=workflow-pilot.yml

Sandbox handoff checklist:

https://github.com/nadeemkamel-arch/workflow-automation-demo-pack/blob/main/handoff_template.md

## Paid Pilot Menu

Good starter projects are intentionally small:

- **Document/API Intake Sprint**: turn sample documents or exports into extracted fields, review routing, staged API payloads, and a runbook.
- **Conversation Flow QA Sprint**: turn draft prompts or customer-message examples into response rules, edge cases, test messages, and handoff notes.
- **Telegram Lead MVP Sprint**: turn a short intake flow into scored leads, AI summary payloads, source tracking, and owner notifications.
- **Workflow Reliability Sprint**: add run logs, retry rules, idempotency checks, incident routes, and a client-ready operations digest.
- **n8n/Python Workflow Rescue Sprint**: fix or prototype one trigger-to-output workflow with sample data, validation, and setup docs.
- **Data Extraction and Report Pack**: convert PDFs, CSVs, spreadsheets, emails, or public pages into a clean report plus a reproducible script.

Most first milestones should use fictional, redacted, or sandbox data and stay in the $75-$300 range unless the scope is already well defined.

## Demos

### n8n AI Ops Triage

Path: `n8n_ai_ops_triage/`

Shows an importable n8n workflow that:

- receives inbound automation requests through a webhook,
- scores requests in a Code node,
- returns a structured action plan through a webhook response,
- keeps customer-facing replies behind review.

Run the contract test:

```bash
cd n8n_ai_ops_triage
python3 -m pytest test_workflow_contract.py
```

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
python3 triage.py --input input/inquiries.csv --out output --today 2026-06-04
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

### Conversation Flow QA

Path: `conversation_flow_qa/`

Turns fictional SMS-style customer replies for an appointment-based beauty studio into:

- intent and risk classification,
- opt-out, complaint, reaction, pricing, and schedule handoff routes,
- a conversation test matrix,
- a JSON run summary.

Run:

```bash
cd conversation_flow_qa
python3 conversation_flow_qa.py --input input/customer_messages.csv --out output
python3 -m pytest test_conversation_flow_qa.py
```

### Document Intake Agent

Path: `document_intake_agent/`

Shows a multi-step document-processing agent flow that turns fictional purchase order, invoice, and contract documents into:

- extracted document fields,
- risk and review routing,
- staged REST API payloads with idempotency keys,
- an agent-style tool trace,
- a Markdown review queue and JSON run summary.

Run:

```bash
cd document_intake_agent
python3 document_intake_agent.py --input-dir input/documents --out output
python3 -m pytest test_document_intake_agent.py
```

### Statement Email Workflow

Path: `statement_email_workflow/`

Shows a database-backed automation pattern that turns fictional session records into:

- SQL-backed weekly statement groups,
- internal pair statements with one CC policy,
- external-recipient statements with another CC policy,
- dry-run email payloads with idempotency keys,
- preview and run-summary outputs.

Run:

```bash
cd statement_email_workflow
python3 statement_email_workflow.py --input input/session_records.csv --out output
python3 -m pytest test_statement_email_workflow.py
```

### Telegram Lead Qualifier

Path: `telegram_lead_qualifier/`

Shows a first-milestone Telegram bot pattern that turns fictional intake answers into:

- scored lead records with referral/source tracking,
- structured AI summary payloads,
- dry-run owner notification payloads,
- consent and off-scope review routes,
- an MVP acceptance report with deferred payment/CRM scope.

Run:

```bash
cd telegram_lead_qualifier
python3 telegram_lead_qualifier.py --input input/lead_intake.csv --out output
python3 -m pytest test_telegram_lead_qualifier.py
```

### Workflow Reliability Monitor

Path: `workflow_reliability_monitor/`

Shows an operations layer for automation handoff that turns fictional workflow run logs into:

- per-run severity and routing,
- retry payloads with idempotency keys,
- duplicate-write and slow-run review paths,
- an incident digest for the workflow owner,
- run-summary metrics for handoff.

Run:

```bash
cd workflow_reliability_monitor
python3 workflow_reliability_monitor.py --input input/flow_runs.csv --out output
python3 -m pytest test_workflow_reliability_monitor.py
```

## Good First Project

A good first milestone is narrow:

- one input source,
- one output format,
- sample or sandbox data,
- basic validation,
- setup notes,
- a review gate before customer-facing actions.

Use `handoff_template.md` to agree on data boundaries, acceptance criteria, validation, and expansion rules before moving from sample data to client systems.

## Boundaries

These demos do not include production credentials, private client data, automatic outbound messages, regulated advice, spam tooling, fake engagement, or platform-rule bypassing.
