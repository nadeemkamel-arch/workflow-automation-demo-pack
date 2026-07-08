# Stripe to QuickBooks Reconciliation Handoff

Fictional sample output. This is a dry-run packet for owner/bookkeeper review, not accounting advice and not a live QuickBooks write.

- Organization: Bright Harbor Happiness Research
- Snapshot date: 2026-07-07
- Payouts reviewed: 3
- Transactions reviewed: 4
- Journal preview lines: 12
- Exceptions: 2
- Launch decision: review_required

## Journal Balance Check

| Payout | Debit | Credit | Balanced |
| --- | ---: | ---: | --- |
| po_usd_clean_0710 | 875.50 | 875.50 | True |
| po_usd_mismatch_0712 | 308.80 | 308.80 | True |

## Review Queue

- `missing_account_rule` on `po_gbp_unmapped_0711` / `txn_2001`: No account rule for charity NEW_FUND in GBP.
- `payout_net_mismatch` on `po_usd_mismatch_0712` / `-`: Computed transaction net 291.20 does not match payout net 290.00.

## Owner Gate

- Confirm each QuickBooks account and class mapping with the bookkeeper before import.
- Confirm how existing Stripe deposits are represented in QuickBooks before creating journal entries.
- Keep API keys, donor names, and account IDs out of public logs.
- Run against a sandbox or exported CSV first; no live writes are enabled in this proof.
