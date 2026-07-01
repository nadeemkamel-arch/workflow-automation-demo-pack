# /intake-scan

Use this when the operator drops in a small batch of inbox items, task notes, CRM rows, or client messages.

## Inputs

- Source type: inbox, meeting notes, CRM export, support requests, or mixed.
- Batch size: 5-15 items.
- Client objective: what the operator wants by the end of the scan.

## Steps

1. Identify the source and timestamp range.
2. Group items into:
   - urgent client-facing,
   - needs operator reply,
   - needs internal task,
   - waiting on someone else,
   - FYI/archive.
3. Extract names, dates, owners, and promised follow-ups.
4. Draft action items without sending or writing externally.
5. Flag missing context and risky assumptions.

## Output

```markdown
## Intake Scan

- Source:
- Range:
- Items reviewed:

### Urgent
| Item | Why it matters | Draft action | Approval needed |
|---|---|---|---|

### Waiting
| Item | Waiting on | Suggested follow-up |
|---|---|---|

### Draft Updates

1. ...

Ready to send/write: no
Approval needed: yes, before any external action
Next human action: review the urgent rows and choose what to send or assign.
```
