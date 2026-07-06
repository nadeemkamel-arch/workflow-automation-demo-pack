# Prelaunch QA Smoke Pack

This public-safe proof turns a small fictional app-testing cycle into outputs a founder can use before sending beta invites.

It is designed for low-friction work: test a product manually, document bugs clearly, separate UX feedback from defects, and give the owner a simple launch gate.

## What It Produces

- `bug_report.csv`: priority, severity, category, device, platform, repro steps, evidence, and recommendation.
- `ux_feedback.md`: the most useful non-code feedback for product polish and trust.
- `retest_checklist.md`: a checklist for verifying fixes and filling missing coverage.
- `test_cycle_summary.json`: severity counts, coverage gaps, readiness score, and launch decision.

## Run

```bash
python3 prelaunch_qa_smoke_pack.py --sessions input/test_sessions.csv --plan input/test_plan.json --out output
python3 -m pytest test_prelaunch_qa_smoke_pack.py
```

## Scope Boundary

This is not a replacement for a full QA team, security review, accessibility audit, or production incident process. It is a fast smoke-test and product-feedback pass for a small app, landing page, signup flow, or beta build.

No private user data, credentials, live customer messages, payments, or production changes are used in this demo. A real client run should start with sandbox data, approved test accounts, and owner review before any public launch.
