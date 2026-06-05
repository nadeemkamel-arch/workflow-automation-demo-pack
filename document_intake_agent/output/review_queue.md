# Document Intake Review Queue

Fictional sample output. API payloads are staged for review, not sent.

| Document | Type | Vendor | Amount | Risk Flags | Route | API Endpoint |
| --- | --- | --- | ---: | --- | --- | --- |
| CON-208 | contract | Atlas Outreach Labs | 3200.00 | outbound_compliance, manager_approval_amount | legal_or_compliance_review | /api/reviews/compliance |
| INV-7781 | invoice | BrightPath Data Services | 420.00 | standard | accounts_payable_queue | /api/ap/invoices |
| PO-1042 | purchase_order | North Coast Event Supply | 1840.00 | deposit_required, rush_timing | manager_review | /api/reviews/manager |

## Launch Gate

- Replace sample documents with approved exports or sandbox files.
- Confirm destination API endpoints, auth scope, and idempotency behavior.
- Keep payment, compliance, and outbound-campaign items in human review.
