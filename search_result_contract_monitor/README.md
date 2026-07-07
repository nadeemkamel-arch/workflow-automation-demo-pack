# Search Result Contract Monitor

Public-safe proof for search API response QA. The example uses fictional response snapshots and a JSON contract to catch parser regressions before customers see broken search results.

## What It Produces

- `output/findings.json`: ranked response-quality findings by ticket, engine, query, severity, and recommendation.
- `output/findings.csv`: spreadsheet-friendly queue for support or engineering triage.
- `output/monitor_summary.json`: release decision and counts by severity/area.
- `output/handoff_note.md`: concise customer-support note explaining what was reproduced and what should happen next.

## Run

```bash
python3 search_result_contract_monitor.py --snapshots input/search_snapshots.json --contract input/result_contract.json --out output
python3 -m pytest test_search_result_contract_monitor.py
# If pytest is not installed:
python3 test_search_result_contract_monitor.py
```

## Why This Matters

Search APIs fail in ways that are easy to miss during fast parser repairs: missing documented blocks, duplicate URLs, non-contiguous positions, empty snippets, access failures, and undocumented shape changes. This gate turns those issues into a reproducible release decision and a clear support handoff.

## Good First Paid Milestone

1. Collect a small set of failing customer tickets, redacted response snapshots, and expected response fields.
2. Build a narrow response contract for one engine or endpoint.
3. Add regression fixtures for the highest-risk parser failures.
4. Return a release decision, ranked issue queue, and support note that explains the customer impact without overpromising.
