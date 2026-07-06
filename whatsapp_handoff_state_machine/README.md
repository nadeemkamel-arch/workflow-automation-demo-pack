# WhatsApp Handoff State Machine

Public-safe proof for small businesses that want AI-drafted WhatsApp or Gmail replies without losing human control.

The demo uses fictional fastener, hotel, clinic, and warehouse messages. It does not connect to WhatsApp, Gmail, AiSensy, Twilio, Make, n8n, Claude, OpenAI, or any live account. The point is the operating pattern:

- classify each inbound message,
- keep risky or active human threads out of AI auto-response,
- draft safe replies into an approval queue,
- create human handoff packets when the conversation needs a person,
- resume AI mode only after a configured inactivity window,
- record that no customer message is sent automatically.

## Run

```bash
python3 whatsapp_handoff_state_machine.py --messages input/messages.csv --rules input/business_rules.json --out output
python3 -m pytest test_whatsapp_handoff_state_machine.py
```

## Outputs

- `output/decision_log.csv`: one route decision per inbound message.
- `output/approval_queue.csv`: drafted replies waiting for owner approval.
- `output/state_table.csv`: current AI/human mode per contact.
- `output/handoff_packets.md`: secretary/owner handoff briefs.
- `output/run_summary.json`: counts and launch gate.

## Client-Safe First Scope

A practical paid first pass would be:

1. Map one channel first: WhatsApp or Gmail, not both.
2. Use sanitized sample messages and test credentials.
3. Define the handoff states: `ai`, `human`, `paused`, `ready_for_review`.
4. Build the approval queue and handoff packet.
5. Connect production only after the owner reviews routing, logs, and failure states.

Starter scope: 2-3 day fixed build or a smaller diagnostic plan before any production credentials are shared.
