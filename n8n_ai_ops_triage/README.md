# n8n AI Ops Triage Workflow

Importable n8n companion workflow for the AI Ops Triage demo.

This workflow shows the orchestration shape a client would expect:

1. Receive a webhook payload of inbound automation requests.
2. Score each request with a Code node.
3. Return a structured triage response for review.

The workflow uses fictional sample data and deterministic logic. It does not call paid APIs, store credentials, send messages, or touch private client data.

## Files

- `workflow.json`: importable n8n workflow.
- `sample_webhook_payload.json`: example request payload.
- `sample_response.json`: expected response shape.
- `test_workflow_contract.py`: verifies the workflow structure and executes the embedded Code node with Node.js.

## Import

1. Open n8n.
2. Import `workflow.json`.
3. Review the webhook path and response node.
4. Test with `sample_webhook_payload.json`.

## Test Locally

```bash
python3 -m pytest test_workflow_contract.py
```

The test does not require a running n8n instance. It validates the JSON contract and runs the Code node logic locally through Node.js.

## Handoff Shape

For a client pilot, pair the exported workflow with:

- one sample webhook payload,
- one expected response,
- one validation command or checklist,
- notes for credentials, retry behavior, and review gates.

See `../handoff_template.md` for the public handoff checklist.

## Client Adaptation

A paid version would replace the sample webhook payload with the client's approved source:

- form submission,
- CRM export,
- Google Sheets row batch,
- internal API payload,
- or another n8n trigger.

Keep a human review step before any customer-facing reply.
