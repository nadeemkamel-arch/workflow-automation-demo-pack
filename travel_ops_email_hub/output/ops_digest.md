# Travel Ops Email Hub Digest

Fictional dry-run output. No Gmail, Slack, Sheets, or booking-engine action was taken.

| Message | Traveler | Booking | Category | Priority | Route | Review |
| --- | --- | --- | --- | --- | --- | --- |
| M-1001 | Maya Singh | unassigned | new_group_request | normal | new_request_queue | New request can receive a draft acknowledgement after duplicate check. |
| M-1002 | Jordan Lee | BR-7781 | hotel_update | normal | supplier_coordination | Hotel or room-block update requires operator review before booking-engine write. |
| M-1003 | Alex Chen | BR-7722 | urgent_traveler_issue | urgent | travel_ops_lead | Urgent travel risk terms detected; Slack alert is dry-run only. |
| M-1004 | Riley Moss | BR-7719 | invoice_or_payment | normal | finance_review | Payment language should not trigger an automatic financial response. |
| M-1005 | Pat Taylor | BR-7708 | hotel_update | normal | supplier_coordination | Hotel or room-block update requires operator review before booking-engine write. |
| M-1006 | Jordan Lee | BR-7781 | hotel_update | normal | supplier_coordination | Hotel or room-block update requires operator review before booking-engine write. |
| M-1007 | Sam Rivera | BR-7790 | urgent_traveler_issue | urgent | travel_ops_lead | Urgent travel risk terms detected; Slack alert is dry-run only. |
| M-1008 | Unknown Vendor | unassigned | unknown_review | review | manual_review | Message does not match the approved travel operations routes. |

## Launch Gate

- Confirm the five email categories and status names before writing to live Sheets.
- Keep Slack alerts dry-run until urgent keywords and on-call ownership are approved.
- Create Gmail drafts only after duplicate and loop-protection checks pass.
- Treat booking-engine writes as staged API payloads until REST docs, auth, and rollback rules are reviewed.
