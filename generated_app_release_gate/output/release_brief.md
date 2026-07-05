# Generated App Release Brief

Decision: `do_not_launch`
Findings: 13

## Counts By Severity

- blocker: 1
- high: 8
- medium: 3
- low: 1

## Highest Priority Findings

- **blocker / schema / /api/lead-summary**: Route references undeclared tables: leads. Regenerate the schema contract or remove stale route references.
- **high / auth / /api/subscriptions/checkout**: Mutating browser-facing route does not declare CSRF protection. Add CSRF/session-origin protection before exposing this route outside preview.
- **high / deployment / healthcheck_path**: Deployment has no healthcheck path. Add a cheap health route and wire it into preview and production checks.
- **high / deployment / rollback_plan**: Deployment has no rollback plan. Document the rollback command, previous build ID, and migration fallback.
- **high / integration / email**: Required environment variables are not declared: RESEND_API_KEY. Declare env vars in the generated app template and preview deployment docs.
- **high / integration / email**: External-write integration is not marked as test/sandbox mode. Keep email, payment, CRM, and other side-effecting integrations in sandbox mode until launch approval.

## Launch Gate

Keep the app in preview until blocker and high findings are resolved, rerun the gate, and attach the generated finding queue to the handoff.
Use sandbox credentials and synthetic data until the owner approves production access, payment webhooks, and external-message sending.
