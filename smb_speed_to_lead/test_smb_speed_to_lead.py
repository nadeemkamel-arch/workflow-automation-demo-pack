from __future__ import annotations

from pathlib import Path

from smb_speed_to_lead import (
    build_payloads,
    build_reactivation_records,
    build_speed_records,
    read_csv,
    run,
    DORMANT_COLUMNS,
    NEW_LEAD_COLUMNS,
)


ROOT = Path(__file__).parent
NEW_LEADS = ROOT / "input" / "new_leads.csv"
DORMANT_CONTACTS = ROOT / "input" / "dormant_contacts.csv"


def test_generic_and_custom_systems_use_http_adapter() -> None:
    records = build_speed_records(read_csv(NEW_LEADS, NEW_LEAD_COLUMNS))
    by_id = {record.record_id: record for record in records}

    assert by_id["SL-1002"].crm_adapter == "http_webhook:generic_adapter"
    assert by_id["SL-1004"].crm_adapter == "http_webhook:generic_adapter"
    assert by_id["SL-1001"].crm_adapter.startswith("native:")


def test_no_consent_and_opt_out_stop_before_outbound() -> None:
    speed = build_speed_records(read_csv(NEW_LEADS, NEW_LEAD_COLUMNS))
    dormant = build_reactivation_records(read_csv(DORMANT_CONTACTS, DORMANT_COLUMNS))
    by_id = {record.record_id: record for record in speed + dormant}

    assert by_id["SL-1003"].route == "manual_review_only"
    assert by_id["SL-1003"].stop_reason == "no_outbound_consent"
    assert by_id["DR-2003"].route == "suppress_all_outbound"
    assert by_id["DR-2003"].stop_reason == "opt_out"


def test_payloads_are_dry_run_or_blocked_with_idempotency() -> None:
    speed = build_speed_records(read_csv(NEW_LEADS, NEW_LEAD_COLUMNS))
    dormant = build_reactivation_records(read_csv(DORMANT_CONTACTS, DORMANT_COLUMNS))
    payloads = build_payloads(speed + dormant)

    assert len(payloads) == 8
    for payload in payloads:
        if payload["status"] == "dry_run_only":
            assert payload["headers"]["X-Dry-Run"] == "true"
            assert payload["headers"]["Idempotency-Key"]
            assert "stopOn" in payload["body"]
        else:
            assert payload["status"] == "blocked_before_outbound"
            assert payload["idempotency_key"]


def test_run_summary_keeps_live_actions_at_zero(tmp_path: Path) -> None:
    summary = run(NEW_LEADS, DORMANT_CONTACTS, tmp_path)

    assert summary["speed_to_lead_records"] == 4
    assert summary["reactivation_records"] == 4
    assert summary["http_webhook_adapter_records"] == 4
    assert summary["live_actions"] == 0
    assert (tmp_path / "config_handoff.md").read_text(encoding="utf-8").startswith("# SMB Speed-to-Lead")
