# Document Intake Agent

Public-safe demo for a multi-step document intake workflow with API-style handoff.

The fictional input documents represent a purchase order, invoice, and contract. The script reads each document, classifies it, extracts core fields, detects risk flags, chooses a review route, builds staged REST API payloads, and writes an agent-style tool trace.

## Outputs

- `output/review_queue.md`: human-readable queue with document type, amount, risk flags, review route, and destination endpoint.
- `output/api_payloads.json`: staged `POST` requests with idempotency keys and review-route headers.
- `output/agent_trace.json`: tool-call style trace for each document.
- `output/run_summary.json`: counts by type and route, plus the API endpoints touched.

## Run

```bash
python3 document_intake_agent.py --input-dir input/documents --out output
python3 -m pytest test_document_intake_agent.py
```

## What This Proves

- Multi-step agent-like workflow design without hiding logic in a black box.
- Document parsing and validation.
- API integration planning with endpoints, headers, idempotency keys, and payload bodies.
- Human review routes for payment, compliance, and outbound-campaign risk.
- Reproducible output and tests.

## Boundaries

This demo does not send API requests, process private documents, approve payments, activate outbound campaigns, or bypass compliance review. Real projects should start with sandbox exports, scoped credentials, redacted samples, and explicit approval before any write action.
