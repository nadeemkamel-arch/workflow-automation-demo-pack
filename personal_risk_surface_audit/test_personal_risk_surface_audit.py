from __future__ import annotations

from pathlib import Path

from personal_risk_surface_audit import analyze_observations, build_review_packets, write_outputs


INPUT = Path(__file__).parent / "input" / "observations.csv"


def test_credential_signal_routes_to_account_security_review() -> None:
    findings = analyze_observations(INPUT)
    finding = next(item for item in findings if item.observation_id == "OBS-1003")

    assert finding.severity == "critical"
    assert finding.route == "account_security_review"
    assert finding.next_action == "verify_and_rotate_secret_with_owner"
    assert finding.live_action_allowed is False


def test_impersonation_signal_stays_manual() -> None:
    findings = analyze_observations(INPUT)
    finding = next(item for item in findings if item.observation_id == "OBS-1002")

    assert finding.severity == "high"
    assert finding.route == "impersonation_review"
    assert finding.live_action_allowed is False


def test_data_broker_profile_routes_to_removal_packet() -> None:
    findings = analyze_observations(INPUT)
    finding = next(item for item in findings if item.observation_id == "OBS-1001")

    assert finding.route == "removal_request_review"
    assert finding.next_action == "prepare_data_broker_removal_packet"


def test_low_confidence_weak_match_is_monitor_only() -> None:
    findings = analyze_observations(INPUT)
    finding = next(item for item in findings if item.observation_id == "OBS-1005")

    assert finding.severity == "low"
    assert finding.route == "monitor"


def test_review_packets_exclude_monitor_items_and_are_dry_run() -> None:
    findings = analyze_observations(INPUT)
    packets = build_review_packets(findings)

    assert len(packets) == 4
    assert all(packet["status"] == "dry_run_only" for packet in packets)
    assert all(packet["requires_owner_approval"] is True for packet in packets)


def test_write_outputs_creates_handoff_files(tmp_path: Path) -> None:
    findings = analyze_observations(INPUT)
    write_outputs(findings, tmp_path)

    assert (tmp_path / "remediation_queue.csv").exists()
    assert (tmp_path / "review_packets.json").exists()
    assert (tmp_path / "audit_summary.md").exists()
    assert (tmp_path / "run_summary.json").exists()
