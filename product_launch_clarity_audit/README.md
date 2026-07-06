# Product Launch Clarity Audit

Public-safe sample for a small product, app, or landing page owner who needs a practical readiness pass before showing users.

The demo uses a fictional travel-planning app and produces:

- a prioritized UX/product issue queue,
- three concrete quick wins,
- a launch-readiness report,
- simple message tests for the homepage or first outreach,
- a machine-readable run summary.

No client data, private analytics, user accounts, or live app access are required for this sample.

## Run

```bash
python3 product_launch_clarity_audit.py --input input/fictional_travel_app.json --out output
python3 -m pytest test_product_launch_clarity_audit.py
```

## Good First Client Scope

For a real first pass, the client can share screenshots, a public URL, or a short product description. The deliverable can stay simple: one report, one issue queue, and the first three changes to make before sending traffic.

