# Conversation Flow QA

Public-safe demo for testing AI conversation rules before a customer-facing SMS workflow goes live.

The fictional input contains customer replies for a luxury beauty or appointment-based studio. The script classifies each message, flags risky cases, chooses a review route, and writes a test matrix that a human operator can review before any automation is connected to a live SMS system.

## Outputs

- `output/conversation_checks.csv`: one row per sample message with intent, risk flags, review route, quality checks, and response rule.
- `output/test_matrix.md`: campaign-level QA matrix for reviewing edge cases.
- `output/run_summary.json`: counts by route and intent, plus IDs that require staff review or suppression.

## Run

```bash
python3 conversation_flow_qa.py --input input/customer_messages.csv --out output
python3 -m pytest test_conversation_flow_qa.py
```

## What This Proves

- Prompt and conversation-rule design can be tested before live deployment.
- Opt-outs, complaints, skin reactions, pricing exceptions, and same-day schedule issues stay out of automatic send paths.
- The deliverable is handoff-friendly: sample data, deterministic checks, test matrix, and clear launch gates.

## Boundaries

This demo does not send texts, scrape customer data, make medical claims, promise discounts, bypass SMS consent rules, or connect to a production booking system. Real projects should use approved brand voice, approved service/pricing text, and the client's SMS compliance process.
