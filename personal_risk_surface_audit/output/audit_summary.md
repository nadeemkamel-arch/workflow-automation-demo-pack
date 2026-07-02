# Personal Risk Surface Audit Summary

Fictional sample output. No live outreach, takedown, scraping, or account action was performed.

| ID | Severity | Route | Source | Signal | Next Action |
| --- | --- | --- | --- | --- | --- |
| OBS-1003 | critical | account_security_review | SnippetBin Example | api_key_like_string | verify_and_rotate_secret_with_owner |
| OBS-1002 | high | impersonation_review | PhotoShare Example | profile_photo | confirm_account_ownership_before_report |
| OBS-1001 | high | removal_request_review | PeopleLookup Example | home_address | prepare_data_broker_removal_packet |
| OBS-1004 | medium | profile_cleanup_review | Old Portfolio Mirror | employment_history | prepare_profile_update_checklist |
| OBS-1005 | low | monitor | Local Forum Example | username | keep_for_periodic_review |

## Launch Gate

- Confirm each match with the account owner before remediation.
- Keep removal, reporting, password reset, and account-security actions manual until approved.
- Treat token-shaped strings as sensitive even when they may be false positives.
- Store real evidence in the client's approved private system, not in a public repo.
