from search_result_contract_monitor import review_snapshots, summarize


def contract():
    return {
        "required_top_level": ["search_information", "organic_results"],
        "organic_required_fields": ["position", "title", "link", "snippet"],
        "minimum_organic_results": 2,
        "allowed_top_level": [
            "api_version",
            "captured_at",
            "customer_ticket",
            "engine",
            "http_status",
            "organic_results",
            "provider",
            "query",
            "search_information",
        ],
        "max_duplicate_links": 0,
        "max_empty_snippet_ratio": 0.25,
    }


def snapshot(**overrides):
    base = {
        "provider": "FictionSearch",
        "engine": "google_light",
        "api_version": "2026-07-07",
        "captured_at": "2026-07-07T17:20:00Z",
        "http_status": 200,
        "query": "test query",
        "customer_ticket": {"id": "TCK-1"},
        "search_information": {"total_results": 10},
        "organic_results": [
            {"position": 1, "title": "A", "link": "https://example.test/a", "snippet": "Alpha"},
            {"position": 2, "title": "B", "link": "https://example.test/b", "snippet": "Beta"},
        ],
    }
    base.update(overrides)
    return base


def test_clean_snapshot_is_release_candidate():
    findings = review_snapshots([snapshot()], contract())

    assert findings == []
    assert summarize([snapshot()], findings)["decision"] == "release_candidate"


def test_missing_top_level_organic_block_holds_release():
    item = snapshot()
    del item["organic_results"]

    findings = review_snapshots([item], contract())
    summary = summarize([item], findings)

    assert any(finding.severity == "blocker" and finding.area == "shape" for finding in findings)
    assert summary["decision"] == "hold_release"


def test_duplicate_links_and_missing_result_field_require_repair():
    item = snapshot(
        organic_results=[
            {"position": 1, "title": "A", "link": "https://example.test/a", "snippet": ""},
            {"position": 1, "title": "B", "link": "https://example.test/a"},
        ]
    )

    findings = review_snapshots([item], contract())
    summary = summarize([item], findings)

    assert any(finding.area == "dedupe" and finding.severity == "high" for finding in findings)
    assert any("missing field" in finding.problem.lower() for finding in findings)
    assert summary["decision"] == "repair_before_release"


def test_access_failure_blocks_even_with_empty_results():
    item = snapshot(http_status=403, organic_results=[])

    findings = review_snapshots([item], contract())

    assert any(finding.area == "access" and finding.severity == "blocker" for finding in findings)
    assert any(finding.area == "coverage" and finding.severity == "blocker" for finding in findings)


def test_undocumented_top_level_block_is_low_risk_note():
    item = snapshot(extra_block={"raw": True})

    findings = review_snapshots([item], contract())

    assert any(finding.area == "shape" and finding.severity == "low" for finding in findings)


if __name__ == "__main__":
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} tests passed")
