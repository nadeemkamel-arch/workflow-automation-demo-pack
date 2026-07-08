# SaaS Onboarding Rescue Sprint

Public-safe proof for early-stage SaaS founders whose trial users sign up, go quiet, and end up in manual spreadsheet follow-up.

The demo turns a fictional trial-user export into a 7-day rescue packet:

- ranked trial-user follow-up queue,
- plain-text onboarding email sequence,
- dry-run CRM/email payloads,
- founder checklist for the first concierge pass,
- machine-readable run summary.

No client accounts, private analytics, live email sends, or CRM credentials are required for this sample.

## Run

```bash
python3 saas_onboarding_rescue.py --users input/trial_users.csv --rules input/email_rules.json --out output
python3 test_saas_onboarding_rescue.py
```

## Good First Client Scope

A tight paid pilot can stay small:

- import a CSV export from Stripe, Clerk, Supabase, Airtable, HubSpot, or a manual spreadsheet,
- identify the first activation event that users fail to reach,
- write 3 to 5 plain-text follow-up emails,
- create a founder review queue,
- hand off dry-run payloads for the client's email or CRM tool.

Keep live sending, domain reputation, unsubscribe compliance, user tracking, and CRM credentials behind a separate launch gate.
