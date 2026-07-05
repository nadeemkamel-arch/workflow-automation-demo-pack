# Agentic Data Pipeline Gate

Decision: `pause_affected_datasets`
Sources reviewed: 7
Findings: 18

## Severity Counts

- blocker: 4
- high: 10
- medium: 4
- low: 0

## Top Repair Items

- **blocker / lead_enrichment_api / CRM-SYNC-007 / schema**: Missing required fields: employee_count. Regenerate or patch the extractor, then run schema tests before publishing the dataset.
- **blocker / public_company_signals / FIN-PDF-002 / schema**: Missing required fields: filing_date. Regenerate or patch the extractor, then run schema tests before publishing the dataset.
- **blocker / public_sector_opportunities / SLED-RFP-004 / access**: Source returned HTTP 403, so the latest run cannot be trusted. Pause downstream refresh, verify allowed access, and rerun from a sanctioned source export or approved connector.
- **blocker / public_sector_opportunities / SLED-RFP-004 / volume**: Observed row count changed by 100.0% versus expected 320. Compare source markup/API shape, sample rejected rows, and keep downstream consumers on the last accepted run.
- **high / public_company_signals / FIN-PDF-002 / drift**: Source content changed and row volume moved materially in the same run. Open an extractor-repair task with before/after samples and require a human review before auto-healing.
- **high / public_company_signals / FIN-PDF-002 / evidence**: Citation/source coverage 72.0% is below required 95.0%. Do not let agent-generated values into review queues without source URLs, row evidence, or document offsets.
- **high / public_company_signals / FIN-PDF-002 / quality**: Null rate 4.1% exceeds limit 3.0%. Trace nulls by field and source section; rerun only after the extraction rule or fallback is fixed.
- **high / public_company_signals / FIN-PDF-002 / volume**: Observed row count changed by 23.6% versus expected 900. Compare source markup/API shape, sample rejected rows, and keep downstream consumers on the last accepted run.

## Launch Gate

Keep affected datasets paused until blocker and high findings are resolved. Agent-generated repairs should produce sample diffs, schema-test results, and cited source evidence before any downstream write or customer-visible export.
