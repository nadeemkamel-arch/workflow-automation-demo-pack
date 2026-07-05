# Generated App Release Gate

Public-safe proof for AI app-builder and AI-built-app rescue work. The example checks a fictional generated web app before launch and turns common AI-generation failure modes into a reviewable queue: auth gaps, webhook replay risk, payment side effects, missing env vars, schema drift, and weak deploy gates.

## What It Produces

- `output/findings.json`: ranked findings with severity, area, route/table/integration, problem, and recommendation.
- `output/finding_queue.csv`: spreadsheet-friendly issue queue for product or engineering review.
- `output/release_brief.md`: owner-readable launch decision and top fixes.
- `output/release_summary.json`: decision, counts by severity, and counts by area.

## Run

```bash
python3 generated_app_release_gate.py --manifest input/generated_app_manifest.json --out output
python3 -m pytest test_generated_app_release_gate.py
```

## Why This Matters

AI-generated apps often look impressive in preview but fail at the boundary between "demo" and "real product": auth rules, payment webhooks, database ownership, env vars, rollback, and observability. This gate makes those boundaries explicit before production credentials, payment writes, or customer traffic are involved.

## Good First Paid Milestone

1. Review one generated app or app-builder template using a redacted manifest or quick repo inventory.
2. Produce a launch decision, ranked finding queue, and smallest safe fix plan.
3. Patch one blocker or high-severity issue.
4. Add a repeatable release check so the app-builder can catch the same class of issue on future generated apps.
