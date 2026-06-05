# Demo: AI Ops Triage Automation

This is a public-safe demo for the Codex micro-studio's automation offer.

It turns a messy queue of inbound requests into:

- a scored CSV,
- a manager-ready action plan,
- draft replies for human review,
- a machine-readable run summary.

The demo uses deterministic scoring rather than a paid LLM call. In a client project, this same shape can sit behind n8n, Make, Zapier, a webhook, or a scheduled Python job. LLM steps can be added where the client approves the tool, data policy, and cost.

## Run

```bash
python3 triage.py --input input/inquiries.csv --out output --today 2026-06-04
python3 -m pytest test_triage.py
```

## Output Files

- `output/triaged_inquiries.csv`
- `output/action_plan.md`
- `output/follow_up_drafts.md`
- `output/run_summary.json`

## What This Proves

- Codex can define a scoped business workflow.
- Codex can build the script, sample data, tests, and handoff notes.
- The workflow keeps a human approval gate before messages go out.
- The implementation avoids secrets, paid APIs, and private client data.

## Client Version

For a real client, the first paid milestone would replace the sample CSV with their actual source:

- Google Sheets export,
- CRM CSV,
- inbox export,
- web form export,
- webhook payload.

The acceptance criteria would stay concrete: produce the agreed output files and pass the validation checklist.
