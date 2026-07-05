# Agentic Data Pipeline Gate

Public-safe proof for AI-generated or agent-repaired data pipelines. The example uses fictional source runs and schema contracts to catch the problems that make generated ETL/RAG/web-data systems untrustworthy: schema drift, missing source evidence, access failures, row-volume shifts, duplicates, stale runs, and unsafe external writes.

## What It Produces

- `output/findings.csv`: ranked findings with severity, dataset, source, area, problem, owner, and recommendation.
- `output/repair_payloads.json`: dry-run agent repair tasks with idempotency keys and human-review requirements.
- `output/validation_report.md`: owner-readable decision, top repair queue, and launch gate.
- `output/run_summary.json`: decision plus counts by severity, dataset, and area.

## Run

```bash
python3 agentic_data_pipeline_gate.py --runs input/source_runs.csv --contract input/schema_contract.json --out output
python3 -m pytest test_agentic_data_pipeline_gate.py
```

## Why This Matters

AI agents can generate useful extraction code and repair suggestions quickly, but the business risk sits downstream: silent schema drift, uncited values, duplicate writes, stale datasets, and external updates that should have stayed in dry-run mode. This gate makes those failure modes inspectable before a dataset reaches analysts, customer workflows, or production integrations.

## Good First Paid Milestone

1. Inventory one generated or agent-repaired data pipeline using redacted run logs and schema expectations.
2. Build a small quality gate for required fields, source evidence, row volume, duplicates, freshness, and write-safety.
3. Patch one blocker or high-severity failure mode.
4. Leave a repeatable check that can run before publish, deploy, or customer handoff.
