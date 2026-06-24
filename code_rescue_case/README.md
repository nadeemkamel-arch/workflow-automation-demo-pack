# AI-Built App Rescue Case

This public-safe case study shows a common app failure: simultaneous API requests each try to refresh an expired token, creating duplicate refreshes and unreliable sessions.

Contents:

- `broken/api-client.mjs`: minimal reproduction of the concurrency bug.
- `fixed/api-client.mjs`: single-flight refresh, validation, and one-retry boundary.
- `test/api-client.test.mjs`: focused regression tests.
- `rescue_report.md`: plain-language diagnosis and handoff note.

Run:

```bash
node --test code_rescue_case/test/api-client.test.mjs
```

The example uses no credentials, external services, or private data.
