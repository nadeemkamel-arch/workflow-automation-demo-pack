# SMB Speed-to-Lead Template

Public-safe proof for reusable small-business automation templates: speed-to-lead and database reactivation.

The demo mirrors a common paid trial scope: a new lead enters through a webhook, an AI step qualifies the request, the workflow replies or routes the lead, and the sequence stops cleanly when consent, reply, opt-out, booking, or owner-review rules require it. It also shows a dormant-contact reactivation sequence with the same stop logic.

## What It Produces

- `workflow_template.json`: n8n-shaped reusable workflow plan with native-node and generic HTTP adapter paths.
- `config.example.json`: client-swappable credentials, endpoints, retry policy, and stop rules.
- `output/speed_to_lead_queue.csv`: new-lead routing plan.
- `output/reactivation_queue.csv`: dormant-contact routing plan.
- `output/dry_run_payloads.json`: staged SMS/email/CRM payloads with idempotency keys and `X-Dry-Run`.
- `output/config_handoff.md`: brief setup and launch notes.
- `output/run_summary.json`: counts, blocked routes, and live-action total.

## Run

```bash
python3 smb_speed_to_lead.py --new-leads input/new_leads.csv --dormant-contacts input/dormant_contacts.csv --out output
python3 -m pytest test_smb_speed_to_lead.py
```

## Client Handoff Notes

Good first paid trial:

- One speed-to-lead workflow with sample lead records.
- One dormant-contact reactivation batch with consent/opt-out stop gates.
- Native CRM path for GoHighLevel or HubSpot where available.
- Generic HTTP webhook path for SMB systems with no native n8n node.
- Dry-run payloads, retry/idempotency notes, and config docs.

Keep live SMS/email sends, CRM credentials, client copy approval, and deliverability rules behind a separate launch gate.
