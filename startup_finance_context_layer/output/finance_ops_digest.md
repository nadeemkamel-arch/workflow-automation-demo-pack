# Startup Finance Context Digest

Fictional sample output. All accounting, payment, task, and customer-facing actions are dry-run only.

| Request | Route | Action | Sources | Missing |
| --- | --- | --- | --- | --- |
| REQ-2001 | ready_for_analyst_review | draft_answer_from_cited_sources | SRC-1003, SRC-1001 | - |
| REQ-2002 | restricted_action_review | review_sources_before_payment_decision | SRC-1002, SRC-1001 | - |
| REQ-2003 | sensitive_context_review | finance_owner_review_required | SRC-1005, SRC-1006 | - |
| REQ-2004 | needs_more_context | ask_for_missing_records | - | invoice |

## Launch Gate

- No payment release without owner approval and source review.
- No accounting-system write until dry-run payloads are inspected.
- Keep sensitive payroll and bank context out of public logs.
- Require cited sources before drafting a client or founder-facing answer.
