from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from charity_stripe_quickbooks_recon import read_rules, reconcile, run


ROOT = Path(__file__).parent
PAYOUTS = ROOT / "input" / "stripe_payout_snapshot.json"
RULES = ROOT / "input" / "account_rules.json"


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_clean_payout_generates_balanced_journal_preview() -> None:
    rows, journal, exceptions, summary = reconcile(_load(PAYOUTS), read_rules(RULES))
    clean_lines = [line for line in journal if line.payout_id == "po_usd_clean_0710"]

    assert len(clean_lines) == 8
    assert {row.review_status for row in rows if row.payout_id == "po_usd_clean_0710"} == {
        "ready_for_bookkeeper_review"
    }
    assert sum(Decimal(line.debit) for line in clean_lines) == sum(Decimal(line.credit) for line in clean_lines)
    assert summary["live_writes_allowed"] is False
    assert not [item for item in exceptions if item.payout_id == "po_usd_clean_0710"]


def test_missing_account_rule_blocks_unmapped_charity_without_journal_lines() -> None:
    rows, journal, exceptions, _summary = reconcile(_load(PAYOUTS), read_rules(RULES))
    row = next(item for item in rows if item.transaction_id == "txn_2001")

    assert row.review_status == "blocked_missing_account_rule"
    assert row.donation_income_account == ""
    assert not [line for line in journal if line.transaction_id == "txn_2001"]
    assert any(item.code == "missing_account_rule" and item.transaction_id == "txn_2001" for item in exceptions)


def test_payout_net_mismatch_is_a_high_severity_exception() -> None:
    _rows, _journal, exceptions, summary = reconcile(_load(PAYOUTS), read_rules(RULES))
    mismatch = next(item for item in exceptions if item.code == "payout_net_mismatch")

    assert mismatch.payout_id == "po_usd_mismatch_0712"
    assert mismatch.severity == "high"
    assert summary["totals_by_payout"]["po_usd_mismatch_0712"]["delta_cents"] == 120
    assert summary["launch_decision"] == "review_required"


def test_write_outputs_creates_review_packet(tmp_path: Path) -> None:
    summary = run(PAYOUTS, RULES, tmp_path)

    assert (tmp_path / "journal_preview.csv").exists()
    assert (tmp_path / "reconciliation_rows.csv").exists()
    assert (tmp_path / "exceptions.json").exists()
    assert (tmp_path / "run_summary.json").exists()
    assert (tmp_path / "handoff_note.md").exists()
    assert summary["journal_line_count"] == 12
    assert summary["exception_count"] == 2


if __name__ == "__main__":
    test_clean_payout_generates_balanced_journal_preview()
    test_missing_account_rule_blocks_unmapped_charity_without_journal_lines()
    test_payout_net_mismatch_is_a_high_severity_exception()
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        test_write_outputs_creates_review_packet(Path(tmp))
