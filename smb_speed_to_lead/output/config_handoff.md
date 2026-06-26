# SMB Speed-to-Lead Template Handoff

Fictional sample output. No SMS, email, CRM, or AI provider calls were sent.

## Reuse Pattern

- Swap credentials and endpoint env vars in `config.example.json`.
- Keep client-specific text, offers, and CRM status names in config.
- Use native n8n nodes where available; use the HTTP webhook adapter when no native node exists.
- Keep `X-Dry-Run` enabled until the client approves test records and stop rules.

## Stop Logic

- No email/SMS consent routes to manual review.
- Opt-out suppresses all outbound attempts.
- Reply, opt-out, booking, or owner stop cancels the remaining sequence.
- Failed CRM or provider calls retry three times, then route to owner review.

## Run Summary

- Speed-to-lead records: 4
- Reactivation records: 4
- Generic HTTP adapter records: 4
- Blocked before outbound: 2