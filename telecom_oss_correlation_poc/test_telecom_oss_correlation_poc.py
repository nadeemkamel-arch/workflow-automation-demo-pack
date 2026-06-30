import csv
import json
import tempfile
import unittest
from pathlib import Path

from telecom_oss_correlation_poc import run


FIXTURE_DIR = Path(__file__).parent


class TelecomOssCorrelationTests(unittest.TestCase):
    def test_correlates_power_dips_to_rfms_alarms(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            summary = run(
                tickets_path=FIXTURE_DIR / "input" / "power_dip_tickets.csv",
                alarms_path=FIXTURE_DIR / "input" / "rfms_alarms.csv",
                gis_path=FIXTURE_DIR / "input" / "gis_sections.csv",
                out_dir=out_dir,
                window_minutes=20,
            )

            self.assertEqual(summary["tickets_seen"], 4)
            self.assertEqual(summary["alarms_seen"], 4)
            self.assertEqual(summary["correlations_found"], 2)
            self.assertEqual(summary["high_confidence"], 2)
            self.assertEqual(summary["live_ticket_updates"], 0)
            self.assertEqual(summary["unmatched_tickets"], ["TT-1011", "TT-1020"])
            self.assertEqual(summary["unmatched_alarms"], ["RF-8827", "RF-8842"])

            with (out_dir / "correlation_results.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(rows[0]["ticket_id"], "TT-1007")
            self.assertEqual(rows[0]["alarm_id"], "RF-8821")
            self.assertEqual(rows[0]["confidence"], "high")
            self.assertEqual(rows[0]["recommended_action"], "prepare linked-ticket note for owner approval")

    def test_writes_review_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            run(
                tickets_path=FIXTURE_DIR / "input" / "power_dip_tickets.csv",
                alarms_path=FIXTURE_DIR / "input" / "rfms_alarms.csv",
                gis_path=FIXTURE_DIR / "input" / "gis_sections.csv",
                out_dir=out_dir,
                window_minutes=20,
            )

            digest = (out_dir / "operator_digest.md").read_text(encoding="utf-8")
            summary = json.loads((out_dir / "run_summary.json").read_text(encoding="utf-8"))

            self.assertIn("Live ticket updates: 0", digest)
            self.assertIn("TT-1007 + RF-8821", digest)
            self.assertEqual(summary["window_minutes"], 20)


if __name__ == "__main__":
    unittest.main()
