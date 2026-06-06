# Property Ops Triage Digest

Fictional dry-run output. No tenant, vendor, Slack, Asana, or QuickBooks action was taken.

| Priority | Property | Unit | Category | Route | Confidence |
| --- | --- | --- | --- | --- | ---: |
| urgent | Cedar Court | 9D | maintenance_request | maintenance_dispatch | 0.86 |
| urgent | Harbor Lofts | 4B | maintenance_request | maintenance_dispatch | 0.86 |
| urgent | Oak Terrace | 7F | maintenance_request | maintenance_dispatch | 0.86 |
| high | Harbor Lofts | not_applicable | invoice_duplicate_review | accounting_review | 0.92 |
| high | Oak Terrace | not_applicable | vendor_invoice | accounting_review | 0.88 |
| normal | Cedar Court | not_applicable | vendor_statement_export | accounting_review | 0.82 |
| normal | Cedar Court | not_applicable | vendor_invoice | accounting_review | 0.88 |
| normal | Harbor Lofts | not_applicable | vendor_invoice | accounting_review | 0.88 |
| normal | Harbor Lofts | 2C | tenant_admin | property_manager_review | 0.78 |
| normal | Oak Terrace | 12A | tenant_admin | property_manager_review | 0.78 |

## Launch Gates

- Confirm categories against 20-50 real redacted messages before enabling live labels.
- Keep tenant/vendor replies in draft mode until manager approval.
- Require idempotency keys before creating Asana tasks or QuickBooks drafts.
- Route duplicate invoice warnings to accounting review only.
