from generated_app_release_gate import review_manifest, summarize


def base_manifest():
    return {
        "routes": [
            {
                "path": "/api/payments",
                "method": "POST",
                "owner": "billing",
                "auth_required": False,
                "tables_read": ["payments"],
                "tables_write": ["payments"],
                "integrations": ["stripe"],
            },
            {
                "path": "/api/webhooks/stripe",
                "method": "POST",
                "owner": "billing",
                "webhook": True,
                "signature_verified": True,
                "idempotent": False,
                "tables_read": ["payments"],
                "tables_write": ["payments"],
                "integrations": ["stripe"],
            },
        ],
        "tables": [
            {
                "name": "payments",
                "has_owner_id": True,
                "has_created_at": True,
                "has_updated_at": False,
            }
        ],
        "integrations": [
            {
                "name": "stripe",
                "required_env": ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"],
                "test_mode": True,
                "writes_external_state": True,
            }
        ],
        "env_declared": ["STRIPE_SECRET_KEY"],
        "deployment": {
            "healthcheck_path": "",
            "migration_strategy": "manual",
            "rollback_plan": "",
            "structured_logs": True,
            "error_boundary": False,
            "custom_domain_ready": False,
        },
    }


def test_payment_mutation_without_auth_is_blocker():
    findings = review_manifest(base_manifest())

    blockers = [finding for finding in findings if finding.severity == "blocker"]
    assert any(finding.area == "auth" and finding.item == "/api/payments" for finding in blockers)


def test_webhook_duplicate_payment_writes_are_high_priority():
    findings = review_manifest(base_manifest())

    assert any(
        finding.severity == "high"
        and finding.area == "payments"
        and finding.item == "/api/webhooks/stripe"
        for finding in findings
    )


def test_missing_env_and_deployment_gates_affect_summary():
    findings = review_manifest(base_manifest())
    summary = summarize(findings)

    assert summary["decision"] == "do_not_launch"
    assert summary["counts_by_severity"]["blocker"] >= 1
    assert summary["counts_by_severity"]["high"] >= 3
    assert summary["counts_by_area"]["deployment"] >= 3


def test_clean_manifest_can_reach_launch_candidate():
    manifest = {
        "routes": [
            {
                "path": "/api/webhooks/stripe",
                "method": "POST",
                "owner": "billing",
                "webhook": True,
                "signature_verified": True,
                "idempotent": True,
                "tables_read": ["payments"],
                "tables_write": ["payments"],
                "integrations": ["stripe"],
            }
        ],
        "tables": [
            {
                "name": "payments",
                "has_owner_id": True,
                "has_created_at": True,
                "has_updated_at": True,
            }
        ],
        "integrations": [
            {
                "name": "stripe",
                "required_env": ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"],
                "test_mode": True,
                "writes_external_state": True,
            }
        ],
        "env_declared": ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"],
        "deployment": {
            "healthcheck_path": "/api/health",
            "migration_strategy": "automated",
            "rollback_plan": "vercel rollback previous-build",
            "structured_logs": True,
            "error_boundary": True,
            "seed_data": True,
            "custom_domain_ready": True,
        },
    }

    assert summarize(review_manifest(manifest))["decision"] == "launch_candidate"
