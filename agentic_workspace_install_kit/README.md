# Agentic Workspace Install Kit

Public-safe proof for an implementation-lead style install: turn a messy operator role into a usable AI coding-agent workspace with repeatable commands, safe tool boundaries, and a client handoff.

The fictional client is a small services team that wants a Claude Code / Codex-style workspace for inbox triage, weekly status reporting, and lightweight CRM follow-up. No private data, API keys, live MCP credentials, or customer records are included.

## What This Demonstrates

- A client-specific `CLAUDE.md` that gives the coding agent role context, workflow boundaries, file map, and stop conditions.
- Slash-command style runbooks for common operator tasks.
- MCP-style integration notes for Gmail, Drive, Slack, ClickUp, and local files without exposing credentials.
- An install checklist that a non-technical operator can follow.
- A 30-day support handoff pattern with recap notes and escalation rules.

## Files

- `CLAUDE.md`: workspace operating instructions for the agent.
- `.claude/commands/intake-scan.md`: reusable command for scanning a small batch of client inputs.
- `.claude/commands/client-recap.md`: reusable command for producing a client-ready recap.
- `mcp_manifest.example.json`: example integration registry with explicit approval gates.
- `sample_client_profile.json`: fictional client profile and allowed data classes.
- `install_checklist.md`: install, training, and support checklist.

## Good First Paid Trial

One client workspace install:

1. collect the client's role, recurring workflows, tools, and data boundaries,
2. create the `CLAUDE.md` and 2-4 slash commands,
3. connect only approved tools or leave placeholder MCP config,
4. train the user on three real workflows,
5. deliver a Loom recap and a 30-day support note.

## Boundaries

- No password, token, OAuth secret, or production credential belongs in the repo.
- Customer-facing sends, CRM writes, payments, account settings, and deletion require explicit approval.
- The first install should use sample, redacted, or screen-shared data until the client accepts the workflow.
