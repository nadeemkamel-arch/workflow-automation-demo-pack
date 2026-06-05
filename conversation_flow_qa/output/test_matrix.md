# Conversation Flow QA Test Matrix

Fictional sample output for reviewing AI conversation rules before any SMS send.

| ID | Campaign Goal | Intent | Risk Flags | Route | Response Rule |
| --- | --- | --- | --- | --- | --- |
| MSG-001 | Help the client choose a new appointment time. | schedule_request | standard | ai_draft_then_human_review | Offer to check availability and ask for two preferred windows. |
| MSG-002 | Help the client choose a new appointment time. | pricing_question | standard | ai_draft_then_human_review | Answer only from the approved service menu and invite the client to choose an add-on. |
| MSG-006 | Answer loyalty questions and keep the client experience high-touch. | schedule_request | standard | ai_draft_then_human_review | Offer to check availability and ask for two preferred windows. |
| MSG-008 | Help the client choose a new appointment time. | unclear_interest | standard | ai_draft_then_human_review | Ask one simple question to clarify interest. |
| MSG-011 | Answer loyalty questions and keep the client experience high-touch. | logistics_question | standard | ai_draft_then_human_review | Provide the approved location detail and ask whether they need parking notes. |
| MSG-010 | Help the client choose a new appointment time. | same_day_schedule_issue | late_arrival | front_desk_review | Route to front desk because timing affects the live calendar. Human review is required before send. |
| MSG-004 | Invite a lapsed client back without pressure. | service_recovery | complaint, medical_or_reaction | human_owner_review | Draft an apology and hand to the owner before any customer reply. Human review is required before send. |
| MSG-007 | Protect client trust after a recent service. | service_recovery | medical_or_reaction | human_owner_review | Draft an apology and hand to the owner before any customer reply. Human review is required before send. |
| MSG-005 | Answer loyalty questions and keep the client experience high-touch. | policy_or_pricing_question | pricing_exception | manager_policy_review | State that a team member will confirm policy before promising a discount or credit. Human review is required before send. |
| MSG-012 | Invite a lapsed client back without pressure. | policy_or_pricing_question | pricing_exception | manager_policy_review | State that a team member will confirm policy before promising a discount or credit. Human review is required before send. |
| MSG-009 | Invite a lapsed client back without pressure. | not_ready | competitor_booked | no_push_follow_up | Acknowledge the choice and avoid pressure or repeated winback messages. |
| MSG-003 | Invite a lapsed client back without pressure. | opt_out | opt_out | suppress_and_confirm | Send a short opt-out confirmation and stop all campaign messages. |

## Launch Gate

- Confirm opt-out handling with the SMS platform before launch.
- Keep complaints, skin reactions, policy exceptions, and same-day timing with staff.
- Test each campaign with approved menu, pricing, location, and booking-policy text.
