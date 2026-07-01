# AI Workspace Install Checklist

## Before The Install

- Confirm the user role and top three recurring workflows.
- Confirm approved tools and data boundaries.
- Collect sample or redacted inputs.
- Create the first `CLAUDE.md` and command set.
- Decide which actions are read-only, draft-only, and approval-gated.

## Live Install

- Place `CLAUDE.md` at the workspace root.
- Add slash commands under `.claude/commands/`.
- Configure MCP placeholders or approved live connections.
- Run one sample intake scan.
- Run one sample client recap.
- Show the user how to approve, reject, or revise drafted actions.

## Training

Train the user on three workflows:

1. daily intake scan,
2. weekly client recap,
3. CRM or task follow-up draft.

For each workflow, show:

- where the input goes,
- what the command does,
- what it refuses to do,
- where approval is required,
- how to save the final handoff.

## 30-Day Support

- First-week check: fix confusing wording and command friction.
- Second-week check: add one new command only if the first two are being used.
- Fourth-week check: review whether the workspace reduced manual work.

## Launch Gate

The workspace is ready for real data only when:

- the user can run the two core commands without coaching,
- approval gates are understood,
- no credential is stored in the repo,
- dry-run outputs match the client's expected workflow.
