# Charity Stripe to QuickBooks Reconciliation

Public-safe proof for a small charity finance automation. The example uses fictional Stripe payout snapshots and account rules to turn consolidated payouts into review-ready QuickBooks journal/import rows, exception flags, and a handoff note.

This is not accounting advice and does not write to Stripe or QuickBooks. It is a dry-run reconciliation pattern for review by the organization and its bookkeeper/accountant.

## What It Produces

- `output/journal_preview.csv`: QuickBooks-style dry-run journal rows for mapped donations, processing fees, and Stripe clearing.
- `output/reconciliation_rows.csv`: transaction-level payout breakdown with mapped accounts, fund/class labels, and review status.
- `output/exceptions.json`: missing account rules, payout amount mismatches, currency issues, and not-ready transactions.
- `output/run_summary.json`: counts, total cents by payout, and a launch decision.
- `output/handoff_note.md`: concise owner/bookkeeper handoff explaining what is safe to review next.

## Run

```bash
python3 charity_stripe_quickbooks_recon.py --payouts input/stripe_payout_snapshot.json --rules input/account_rules.json --out output
python3 -m pytest test_charity_stripe_quickbooks_recon.py
# If pytest is not installed:
python3 test_charity_stripe_quickbooks_recon.py
```

## Why This Matters

Stripe payouts often arrive in QuickBooks as one consolidated deposit. For multi-charity or multi-fund organizations, that can hide the individual donations, processing fees, currency differences, and fund restrictions that need review. This proof turns those hidden pieces into a reproducible dry-run queue before anyone changes the accounting system.

## Good First Paid Milestone

1. Export one recent Stripe payout and the current QuickBooks chart-of-accounts/fund mapping.
2. Build a dry-run reconciliation that maps each donation and fee to the intended account/class.
3. Flag any unmapped charity, payout mismatch, refund, pending transaction, or multi-currency issue.
4. Return a journal/import preview, exception queue, and handoff note for bookkeeper review.
