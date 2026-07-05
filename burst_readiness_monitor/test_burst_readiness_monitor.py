from __future__ import annotations

import json
from pathlib import Path

from burst_readiness_monitor import analyze_endpoints, peak_total_rps, write_outputs


FIXTURE = Path("input/traffic_windows.csv")


def test_analyze_endpoints_flags_launch_blockers() -> None:
    records = analyze_endpoints(FIXTURE)
    by_endpoint = {record.endpoint: record for record in records}

    assert by_endpoint["ticket_waitlist"].severity == "critical"
    assert by_endpoint["ticket_waitlist"].route == "launch_blocker"
    assert by_endpoint["media_upload"].severity == "critical"
    assert by_endpoint["homepage"].severity == "ok"
    assert by_endpoint["event_discovery"].cost_per_1k_requests_usd > 0.075


def test_peak_total_rps_meets_target() -> None:
    assert peak_total_rps(FIXTURE, window_seconds=60) == 545.0


def test_write_outputs_creates_review_artifacts(tmp_path: Path) -> None:
    records = analyze_endpoints(FIXTURE)
    write_outputs(records, tmp_path, source_path=FIXTURE, target_rps=500, window_seconds=60)

    readiness = (tmp_path / "endpoint_readiness.csv").read_text(encoding="utf-8")
    brief = (tmp_path / "load_test_brief.md").read_text(encoding="utf-8")
    alerts = json.loads((tmp_path / "alert_payloads.json").read_text(encoding="utf-8"))
    summary = json.loads((tmp_path / "run_summary.json").read_text(encoding="utf-8"))

    assert "ticket_waitlist" in readiness
    assert "Target met in sample: yes" in brief
    assert any(alert["body"]["endpoint"] == "media_upload" for alert in alerts)
    assert summary["target_met"] is True
    assert summary["severity_counts"]["critical"] == 2
