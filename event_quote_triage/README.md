# Event Quote Triage Demo

Public-safe sample for event rental quote intake. This demo turns fictional wishlist requests into staff-ready quote checklists, missing-info prompts, and a run summary.

The target use case is a small events business that receives quote requests with event details, wishlist items, delivery/setup notes, and incomplete customer context.

## Inputs

`input/event_requests.csv`

Required columns:

- `id`
- `event_name`
- `event_date`
- `event_type`
- `wishlist_items`
- `guest_count`
- `city`
- `venue_address`
- `delivery_window`
- `setup_notes`
- `budget_notes`

## Outputs

Generated into `output/`:

- `quote_checklist.csv`: one staff-ready row per request.
- `staff_brief.md`: readable checklist for manual review.
- `run_summary.json`: total counts by readiness and delivery flag.

## Run

```bash
python3 event_quote_triage.py --input input/event_requests.csv --out output
```

## Validate

```bash
python3 -m pytest test_event_quote_triage.py
```

## Boundaries

- Fictional sample data only.
- No customer records.
- No credentials.
- No automatic customer messages.
- No payment, deposit, booking, or SMS automation.
