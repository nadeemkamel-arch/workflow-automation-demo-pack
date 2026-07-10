# Agentic Workflow Automation Demo Pack

Public-safe demos for scoped automation work: n8n workflow JSON, Python scripts, API handoff payloads, document-processing flows, finance reconciliation packets, product launch clarity audits, prelaunch QA smoke tests, search API response checks, telecom OSS correlation, travel-ops email routing, reproducible outputs, tests, and handoff notes.

These examples use fictional data so the code, outputs, and runbooks can be inspected publicly. The same delivery shape can connect to approved client systems such as Google Sheets exports, CRM CSVs, webhooks, REST APIs, LLM calls, or n8n/Make/Zapier workflows once the data source, credentials, cost controls, and launch gate are agreed.

Portfolio page:

https://nadeemkamel-arch.github.io/workflow-automation-demo-pack/

Student resume and application starter page:

https://nadeemkamel-arch.github.io/workflow-automation-demo-pack/summer-job/

Free workflow fit check:

https://github.com/nadeemkamel-arch/workflow-automation-demo-pack/issues/new?template=workflow-fit-check.yml

Paid sprint inquiry form:

https://github.com/nadeemkamel-arch/workflow-automation-demo-pack/issues/new?template=workflow-pilot.yml

QA smoke-test inquiry form:

https://github.com/nadeemkamel-arch/workflow-automation-demo-pack/issues/new?template=qa-smoke-test.yml

AI-Built App Rescue:

https://nadeemkamel-arch.github.io/workflow-automation-demo-pack/code-rescue/

Code rescue inquiry form:

https://github.com/nadeemkamel-arch/workflow-automation-demo-pack/issues/new?template=code-rescue.yml

Sandbox handoff checklist:

https://github.com/nadeemkamel-arch/workflow-automation-demo-pack/blob/main/handoff_template.md

Delivery notes:

https://github.com/nadeemkamel-arch/workflow-automation-demo-pack/blob/main/DELIVERY_NOTES.md

## Featured Offer: $95 Workflow Rescue Sprint

Start with the free fit check: share one fictional, redacted, or high-level example.
Within one business day, the response will say whether it fits the fixed sprint, needs
a different scope, or is not a fit. There is no charge and no obligation to continue.

Send one broken or manual workflow. The fixed starter scope covers one input, one
output, one main failure path, and delivery within three business days.

Delivery includes:

- a working first fix or prototype,
- a focused test or validation command,
- setup and handoff notes,
- a plain-language list of what changed.

Start with a fictional, redacted, or sandbox example. No production credentials are
needed. If the workflow is larger than the starter scope, that is identified before
work begins.

Inquiry form:

https://github.com/nadeemkamel-arch/workflow-automation-demo-pack/issues/new?template=workflow-pilot.yml

## Other Proofed Capabilities

Good starter projects are intentionally small:

- **AI-Built App Rescue**: diagnose and fix one reproducible bug in a small React, TypeScript, JavaScript, or Python project, with a focused test and handoff. Fixed starter scope: $75.
- **Product Launch Clarity Audit**: turn a small app, landing page, or prototype into a ranked issue queue, three quick wins, message tests, and a readiness report.
- **Prelaunch QA Smoke Test**: test a small app, signup flow, or beta build and return a bug report, UX notes, retest checklist, and launch gate.
- **Document/API Intake Sprint**: turn sample documents or exports into extracted fields, review routing, staged API payloads, and a runbook.
- **Conversation Flow QA Sprint**: turn draft prompts or customer-message examples into response rules, edge cases, test messages, and handoff notes.
- **WhatsApp/Gmail Handoff Sprint**: turn inbound messages into AI draft approvals, human-handoff packets, pause/resume state, and no-auto-send logs.
- **Telegram Lead MVP Sprint**: turn a short intake flow into scored leads, AI summary payloads, source tracking, and owner notifications.
- **SMB Speed-to-Lead Sprint**: turn new-lead and dormant-contact samples into reusable n8n-style workflow templates with CRM adapters, consent/opt-out stop gates, dry-run payloads, and config docs.
- **SaaS Onboarding Rescue Sprint**: turn a trial-user export into a ranked follow-up queue, plain-text activation emails, dry-run CRM/email payloads, and a founder review checklist.
- **Telecom OSS Correlation PoC**: correlate OSS tickets, RFMS alarms, and GIS equipment mapping into a review-ready queue with no live ticket updates.
- **Property Ops Triage Sprint**: turn sample tenant/vendor inbox messages into maintenance routes, invoice review packets, dry-run task payloads, and owner digests.
- **Travel Ops Email Hub Sprint**: turn sample travel-agency emails into Sheets status rows, Slack urgent alerts, draft auto-replies, booking API payloads, and launch gates.
- **Workflow Reliability Sprint**: add run logs, retry rules, idempotency checks, incident routes, and a client-ready operations digest.
- **Burst Readiness Sprint**: turn load-test samples and traffic logs into endpoint risk rankings, alert payloads, cost flags, and launch gates before a beta or campaign spike.
- **Startup Finance Context Layer**: turn messy finance records into cited context packets, dry-run task/accounting payloads, and review gates before any money movement.
- **Charity Stripe to QuickBooks Reconciliation**: turn consolidated Stripe payout exports into transaction-level donation, fee, clearing-account, exception, and bookkeeper-review packets.
- **Personal Risk Surface Audit**: turn approved public-risk observations into a ranked remediation queue, dry-run review packets, and account-owner launch gates.
- **Agentic Workspace Install**: set up a Claude Code / Codex-style workspace with `CLAUDE.md`, slash commands, MCP-style integration notes, approval gates, training steps, and support handoff.
- **Generated App Release Gate**: review an AI-generated app manifest for auth, payment, webhook, schema, env, and deployment blockers before production launch.
- **Agentic Data Pipeline Gate**: validate agent-generated extraction/RAG/data pipelines for schema drift, source evidence, row-volume shifts, duplicate keys, stale runs, and write-safety before publish.
- **Agent Capability Eval Loop**: turn capability-agent telemetry into eval findings, monitoring summaries, iteration tasks, and a handoff brief before a limited pilot.
- **Search Result Contract Monitor**: check search API response snapshots for missing documented blocks, duplicate links, ranking gaps, empty snippets, access failures, and support-ready release decisions.
- **n8n/Python Workflow Rescue Sprint**: fix or prototype one trigger-to-output workflow with sample data, validation, and setup docs.
- **Data Extraction and Report Pack**: convert PDFs, CSVs, spreadsheets, emails, or public pages into a clean report plus a reproducible script.

Most first milestones should use fictional, redacted, or sandbox data and stay in the $75-$300 range unless the scope is already well defined.

## Demos

### FPGA Determinant Accelerator

Path: `eda_determinant_accelerator/`

Shows a small EDA/digital-design portfolio sample:

- SystemVerilog RTL determinant accelerator.
- Ready/valid row-major input stream.
- Signed arithmetic and shared iterative divider.
- ARM64/C golden model.
- Verilator C++ simulation harness.
- Directed and randomized verification with 108/108 RTL cases passing.
- Yosys latency and resource-report excerpts.

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

### Agentic Workspace Install Kit

Path: `agentic_workspace_install_kit/`

Shows an implementation-lead install pattern for a fictional operator:

- client-specific `CLAUDE.md`,
- reusable slash commands,
- MCP-style integration manifest,
- explicit approval gates,
- install, training, and 30-day support checklist.

Inspect:

```bash
cd agentic_workspace_install_kit
find . -maxdepth 3 -type f | sort
```

### SaaS Onboarding Rescue Sprint

Path: `saas_onboarding_rescue/`

Shows a 7-day rescue packet for early-stage SaaS teams whose trial users sign up, go quiet, and end up in manual spreadsheet follow-up.

- synthetic trial-user CSV,
- ranked activation follow-up queue,
- plain-text email sequence,
- dry-run CRM/email payloads,
- founder launch checklist and no-live-send summary.

Run:

```bash
cd saas_onboarding_rescue
python3 saas_onboarding_rescue.py --users input/trial_users.csv --rules input/email_rules.json --out output
python3 test_saas_onboarding_rescue.py
```

### Generated App Release Gate

Path: `generated_app_release_gate/`

Shows an AI-app-builder quality gate that turns a generated app manifest into:

- auth, payment, webhook, schema, env, and deploy findings,
- a launch/no-launch decision,
- a spreadsheet-friendly issue queue,
- a short release brief for owner review.

Run:

```bash
cd generated_app_release_gate
python3 generated_app_release_gate.py --manifest input/generated_app_manifest.json --out output
python3 -m pytest test_generated_app_release_gate.py
```

### Product Launch Clarity Audit

Path: `product_launch_clarity_audit/`

Shows a practical pre-launch review for a small app or landing page:

- ranked UX/product issue queue,
- three concrete quick wins,
- homepage/message test options,
- readiness score and launch decision,
- owner review gate before broad launch.

Run:

```bash
cd product_launch_clarity_audit
python3 product_launch_clarity_audit.py --input input/fictional_travel_app.json --out output
python3 -m pytest test_product_launch_clarity_audit.py
```

### Prelaunch QA Smoke Pack

Path: `prelaunch_qa_smoke_pack/`

Shows a small beta-test pass for a fictional habit app:

- mobile and desktop test-session intake,
- severity-ranked bug report,
- practical UX feedback,
- retest checklist,
- readiness score and beta launch gate.

Run:

```bash
cd prelaunch_qa_smoke_pack
python3 prelaunch_qa_smoke_pack.py --sessions input/test_sessions.csv --plan input/test_plan.json --out output
python3 -m pytest test_prelaunch_qa_smoke_pack.py
```

### Agentic Data Pipeline Gate

Path: `agentic_data_pipeline_gate/`

Shows a quality gate for generated or agent-repaired data pipelines:

- schema and primary-key contract checks,
- source citation/evidence coverage,
- row-volume, duplicate, null-rate, and freshness checks,
- dry-run repair payloads with idempotency keys,
- owner-readable validation report and publish gate.

Run:

```bash
cd agentic_data_pipeline_gate
python3 agentic_data_pipeline_gate.py --runs input/source_runs.csv --contract input/schema_contract.json --out output
python3 -m pytest test_agentic_data_pipeline_gate.py
```

### Search Result Contract Monitor

Path: `search_result_contract_monitor/`

Shows a search API response QA gate that turns fictional customer-ticket snapshots into:

- missing documented block and field findings,
- duplicate link, ranking, snippet, and access checks,
- a release/repair/hold decision,
- a support-ready handoff note.

Run:

```bash
cd search_result_contract_monitor
python3 search_result_contract_monitor.py --snapshots input/search_snapshots.json --contract input/result_contract.json --out output
python3 -m pytest test_search_result_contract_monitor.py
```

### Charity Stripe to QuickBooks Reconciliation

Path: `charity_stripe_quickbooks_recon/`

Shows a dry-run finance-ops reconciliation for a fictional charity:

- Stripe payout snapshot intake,
- account/class mapping rules,
- transaction-level donation and fee breakdown,
- QuickBooks-style journal preview rows,
- exception queue for missing rules and payout mismatches,
- owner/bookkeeper review gate before any accounting-system write.

Run:

```bash
cd charity_stripe_quickbooks_recon
python3 charity_stripe_quickbooks_recon.py --payouts input/stripe_payout_snapshot.json --rules input/account_rules.json --out output
python3 -m pytest test_charity_stripe_quickbooks_recon.py
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

### WhatsApp Handoff State Machine

Path: `whatsapp_handoff_state_machine/`

Shows a small service-business approval loop for WhatsApp or Gmail messages:

- AI mode vs. human mode per contact,
- risky-message and handoff keyword routing,
- AI-drafted replies held for owner approval,
- human handoff packets for a secretary or manager,
- auto-resume after an inactivity window,
- zero automatic customer sends.

Run:

```bash
cd whatsapp_handoff_state_machine
python3 whatsapp_handoff_state_machine.py --messages input/messages.csv --rules input/business_rules.json --out output
python3 -m pytest test_whatsapp_handoff_state_machine.py
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

### Telecom OSS Correlation PoC

Path: `telecom_oss_correlation_poc/`

Shows a telecom operations automation pattern that turns fictional OSS power-dip tickets, RFMS alarms, and GIS equipment mapping into:

- matched ticket/alarm correlations,
- confidence scoring,
- unmatched-ticket and unmatched-alarm queues,
- an operator digest,
- a JSON run summary with zero live ticket updates.

Run:

```bash
cd telecom_oss_correlation_poc
python3 telecom_oss_correlation_poc.py --tickets input/power_dip_tickets.csv --alarms input/rfms_alarms.csv --gis input/gis_sections.csv --out output
python3 -m unittest test_telecom_oss_correlation_poc.py
```

### Travel Ops Email Hub

Path: `travel_ops_email_hub/`

Shows a B2B travel-agency automation pattern that turns fictional inbox messages into:

- Gmail-style email classification,
- Google Sheets status rows,
- Slack urgent-travel alerts,
- draft auto-replies with loop-protection keys,
- staged booking-engine REST payloads,
- an operations digest and run summary with zero live actions.

Run:

```bash
cd travel_ops_email_hub
python3 travel_ops_email_hub.py --input input/travel_messages.csv --out output
python3 -m pytest test_travel_ops_email_hub.py
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

### Property Ops Triage

Path: `property_ops_triage/`

Shows a property-management inbox automation pattern that turns fictional tenant/vendor messages into:

- maintenance, tenant-admin, vendor-invoice, statement-export, and duplicate-invoice routes,
- dry-run Asana-style task payloads,
- vendor invoice review packets with staged QuickBooks-style draft payloads,
- Slack-style owner digest with launch gates,
- idempotency keys and no live tenant/vendor/accounting actions.

Run:

```bash
cd property_ops_triage
python3 property_ops_triage.py --input input/property_messages.csv --out output
python3 -m pytest test_property_ops_triage.py
```

### SMB Speed-to-Lead Template

Path: `smb_speed_to_lead/`

Shows a reusable small-business automation pattern that turns fictional new leads and dormant contacts into:

- speed-to-lead and database-reactivation routing queues,
- native CRM or generic HTTP webhook adapter choices,
- consent and opt-out stop gates,
- dry-run SMS/email/CRM payloads with idempotency keys,
- config docs for swapping client credentials and endpoints.

Run:

```bash
cd smb_speed_to_lead
python3 smb_speed_to_lead.py --new-leads input/new_leads.csv --dormant-contacts input/dormant_contacts.csv --out output
python3 -m pytest test_smb_speed_to_lead.py
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

### Burst Readiness Monitor

Path: `burst_readiness_monitor/`

Shows a load-test and monitoring readiness layer that turns fictional traffic windows into:

- endpoint-level severity and owner routing,
- peak RPS and target-readiness summary,
- latency, error-rate, cache, and cost flags,
- dry-run alert payloads with idempotency keys,
- launch gates before a beta, event, or campaign spike.

Run:

```bash
cd burst_readiness_monitor
python3 burst_readiness_monitor.py --input input/traffic_windows.csv --out output --target-rps 500
python3 -m pytest test_burst_readiness_monitor.py
```

### Personal Risk Surface Audit

Path: `personal_risk_surface_audit/`

Shows a privacy/security-adjacent review workflow that turns fictional web-risk observations into:

- severity, route, and next-action classification,
- data-broker, impersonation, credential, stale-profile, and weak-match handling,
- dry-run analyst review packets,
- owner-readable launch gates,
- run-summary metrics for handoff.

Run:

```bash
cd personal_risk_surface_audit
python3 personal_risk_surface_audit.py --input input/observations.csv --out output
python3 -m pytest test_personal_risk_surface_audit.py
```

### Startup Finance Context Layer

Path: `startup_finance_context_layer/`

Shows an accounting/finance operator context layer that turns fictional source records and operator requests into:

- cited context packets,
- dry-run task/accounting payloads,
- payment and sensitive-record review gates,
- missing-context routing,
- run-summary metrics for handoff.

Run:

```bash
cd startup_finance_context_layer
python3 finance_context_layer.py --records input/source_records.csv --requests input/operator_requests.csv --out output
python3 -m pytest test_finance_context_layer.py
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
