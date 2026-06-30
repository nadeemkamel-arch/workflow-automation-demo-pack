# Telecom OSS Correlation PoC

Public-safe proof for a telecom operations pattern: correlate OSS power-dip tickets with RFMS alarms through a GIS equipment map, then produce an operator review queue.

The demo mirrors a practical first PoC scope for n8n/Python/PostgreSQL-style automation work:

- ingest power-dip trouble tickets,
- ingest RFMS/site alarm events,
- map equipment to GIS sections,
- correlate events by section and time window,
- score confidence,
- write a review-ready CSV and operator digest,
- keep all live OSS updates behind a separate approval gate.

## What It Produces

- `output/correlation_results.csv`: matched ticket/alarm rows with confidence and recommended action.
- `output/operator_digest.md`: plain-language summary for operations review.
- `output/run_summary.json`: counts, unmatched items, and live-action total.

## Run

```bash
python3 telecom_oss_correlation_poc.py --tickets input/power_dip_tickets.csv --alarms input/rfms_alarms.csv --gis input/gis_sections.csv --out output
python3 -m unittest test_telecom_oss_correlation_poc.py
```

## Client Handoff Notes

Good first paid trial:

- One sample extract from OSS tickets.
- One sample extract from RFMS alarms.
- One GIS/equipment mapping table.
- One agreed time window for correlation.
- Dry-run output only, with no ticket updates until the buyer approves the rules.

Expansion options after the first review:

- PostgreSQL staging tables and indexes.
- n8n webhook/manual-trigger wrapper.
- Slack or email digest for exceptions.
- Dashboard summary grouped by region, section, or severity.
- Safe update step for ticket comments after explicit approval.
