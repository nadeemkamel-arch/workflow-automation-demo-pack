from agentic_data_pipeline_gate import review_runs, summarize


def contract():
    return {
        "dataset": {
            "required_fields": ["id", "name", "source_url", "captured_at"],
            "primary_key": "id",
            "max_null_rate": 0.02,
            "min_citation_coverage": 0.95,
            "max_row_delta_ratio": 0.1,
            "external_write_allowed": False,
        }
    }


def row(**overrides):
    base = {
        "source_id": "SRC-1",
        "dataset": "dataset",
        "source_type": "html",
        "extractor_version": "v1",
        "expected_rows": 100,
        "observed_rows": 100,
        "observed_fields": "id|name|source_url|captured_at",
        "primary_key": "id",
        "duplicate_key_count": 0,
        "null_rate": 0.0,
        "citation_coverage": 1.0,
        "http_status": 200,
        "content_hash_changed": False,
        "last_success_hours": 1,
        "owner": "owner",
        "external_write": False,
    }
    base.update(overrides)
    return base


def test_missing_required_field_blocks_dataset():
    findings = review_runs([row(observed_fields="id|name|captured_at")], contract())

    assert any(finding.severity == "blocker" and finding.area == "schema" for finding in findings)


def test_access_blocker_and_volume_blocker_pause_dataset():
    findings = review_runs([row(http_status=403, observed_rows=0, citation_coverage=0.0)], contract())
    summary = summarize([row()], findings)

    assert summary["decision"] == "pause_affected_datasets"
    assert summary["counts_by_severity"]["blocker"] >= 2


def test_low_citation_coverage_requires_repair_before_publish():
    findings = review_runs([row(citation_coverage=0.7)], contract())
    summary = summarize([row()], findings)

    assert any(finding.area == "evidence" and finding.severity == "high" for finding in findings)
    assert summary["decision"] == "repair_before_publish"


def test_clean_run_is_publish_candidate():
    findings = review_runs([row()], contract())

    assert findings == []
    assert summarize([row()], findings)["decision"] == "publish_candidate"


def test_external_write_against_read_only_contract_blocks():
    findings = review_runs([row(external_write=True)], contract())

    assert any(finding.area == "write_gate" and finding.severity == "blocker" for finding in findings)
