#!/usr/bin/env python3
"""Release gate for AI-generated app manifests.

This is a public-safe proof artifact: it checks a fictional generated app
manifest for issues that commonly block AI app builders from shipping safely.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


SEVERITY_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
PAYMENT_TERMS = {"stripe", "paypal", "billing", "checkout", "payment", "payments"}


@dataclass(frozen=True)
class Finding:
    severity: str
    area: str
    item: str
    problem: str
    recommendation: str


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        return json.load(handle)


def has_payment_signal(route: dict[str, Any]) -> bool:
    haystack = " ".join(
        [
            route.get("path", ""),
            route.get("owner", ""),
            " ".join(route.get("integrations", [])),
            " ".join(route.get("tables_write", [])),
        ]
    ).lower()
    return any(term in haystack for term in PAYMENT_TERMS)


def add_finding(
    findings: list[Finding],
    severity: str,
    area: str,
    item: str,
    problem: str,
    recommendation: str,
) -> None:
    findings.append(Finding(severity, area, item, problem, recommendation))


def review_routes(manifest: dict[str, Any], findings: list[Finding]) -> None:
    known_tables = {table["name"] for table in manifest.get("tables", [])}
    known_integrations = {item["name"] for item in manifest.get("integrations", [])}

    for route in manifest.get("routes", []):
        path = route["path"]
        method = route.get("method", "GET").upper()
        writes_tables = route.get("tables_write", [])
        integrations = route.get("integrations", [])

        if method in MUTATING_METHODS and not route.get("webhook") and not route.get("auth_required"):
            add_finding(
                findings,
                "blocker",
                "auth",
                path,
                "Mutating route is callable without authentication.",
                "Require an authenticated session or move the action behind a signed webhook.",
            )

        if method in MUTATING_METHODS and not route.get("webhook") and not route.get("csrf_protected"):
            add_finding(
                findings,
                "high",
                "auth",
                path,
                "Mutating browser-facing route does not declare CSRF protection.",
                "Add CSRF/session-origin protection before exposing this route outside preview.",
            )

        if route.get("role_required") and not route.get("auth_required"):
            add_finding(
                findings,
                "blocker",
                "auth",
                path,
                "Role-gated route is missing the base authentication gate.",
                "Enforce authentication before checking role claims.",
            )

        missing_tables = sorted((set(route.get("tables_read", [])) | set(writes_tables)) - known_tables)
        if missing_tables:
            add_finding(
                findings,
                "blocker",
                "schema",
                path,
                f"Route references undeclared tables: {', '.join(missing_tables)}.",
                "Regenerate the schema contract or remove stale route references.",
            )

        missing_integrations = sorted(set(integrations) - known_integrations)
        if missing_integrations:
            add_finding(
                findings,
                "high",
                "integration",
                path,
                f"Route references undeclared integrations: {', '.join(missing_integrations)}.",
                "Add integration configuration, env requirements, and dry-run behavior.",
            )

        if route.get("webhook") and not route.get("signature_verified"):
            add_finding(
                findings,
                "blocker",
                "webhook",
                path,
                "Webhook route does not declare signature verification.",
                "Verify provider signatures before reading or writing any state.",
            )

        if route.get("webhook") and not route.get("idempotent"):
            add_finding(
                findings,
                "high",
                "webhook",
                path,
                "Webhook route writes state without an idempotency guarantee.",
                "Store provider event IDs and make repeated webhook delivery a no-op.",
            )

        if has_payment_signal(route) and method in MUTATING_METHODS:
            if not route.get("auth_required") and not route.get("webhook"):
                add_finding(
                    findings,
                    "blocker",
                    "payments",
                    path,
                    "Payment-adjacent mutation is neither authenticated nor a signed webhook.",
                    "Require auth for customer checkout routes and signatures for webhook routes.",
                )
            if "payments" in writes_tables and not route.get("idempotent") and route.get("webhook"):
                add_finding(
                    findings,
                    "high",
                    "payments",
                    path,
                    "Payment webhook can duplicate payment writes.",
                    "Use event IDs, unique payment provider IDs, and replay tests.",
                )


def review_tables(manifest: dict[str, Any], findings: list[Finding]) -> None:
    for table in manifest.get("tables", []):
        name = table["name"]
        if not table.get("has_owner_id"):
            add_finding(
                findings,
                "high",
                "schema",
                name,
                "Table does not declare an owner or tenant column.",
                "Add owner_id/account_id and verify every query scopes by it.",
            )
        if not table.get("has_created_at"):
            add_finding(
                findings,
                "medium",
                "schema",
                name,
                "Table does not declare a created_at timestamp.",
                "Add creation timestamps for debugging, support, and audit trails.",
            )
        if not table.get("has_updated_at"):
            add_finding(
                findings,
                "medium",
                "schema",
                name,
                "Table does not declare an updated_at timestamp.",
                "Add updated_at so generated admin screens and support audits have context.",
            )


def review_integrations(manifest: dict[str, Any], findings: list[Finding]) -> None:
    declared_env = set(manifest.get("env_declared", []))
    for integration in manifest.get("integrations", []):
        name = integration["name"]
        missing_env = sorted(set(integration.get("required_env", [])) - declared_env)
        if missing_env:
            add_finding(
                findings,
                "high",
                "integration",
                name,
                f"Required environment variables are not declared: {', '.join(missing_env)}.",
                "Declare env vars in the generated app template and preview deployment docs.",
            )
        if integration.get("writes_external_state") and not integration.get("test_mode"):
            add_finding(
                findings,
                "high",
                "integration",
                name,
                "External-write integration is not marked as test/sandbox mode.",
                "Keep email, payment, CRM, and other side-effecting integrations in sandbox mode until launch approval.",
            )


def review_deployment(manifest: dict[str, Any], findings: list[Finding]) -> None:
    deploy = manifest.get("deployment", {})
    checks = [
        ("healthcheck_path", "high", "Deployment has no healthcheck path.", "Add a cheap health route and wire it into preview and production checks."),
        ("rollback_plan", "high", "Deployment has no rollback plan.", "Document the rollback command, previous build ID, and migration fallback."),
        ("error_boundary", "medium", "App shell has no error boundary.", "Add a generated error boundary so broken pages fail with useful diagnostics."),
        ("custom_domain_ready", "low", "Custom-domain readiness is not confirmed.", "Confirm DNS, HTTPS, and route base URLs before custom-domain launch."),
    ]
    for key, severity, problem, recommendation in checks:
        if not deploy.get(key):
            add_finding(findings, severity, "deployment", key, problem, recommendation)

    if deploy.get("migration_strategy") == "manual":
        add_finding(
            findings,
            "medium",
            "deployment",
            "migration_strategy",
            "Migrations are manual, which is fragile for generated preview apps.",
            "Generate a migration command and a dry-run migration check in the deploy pipeline.",
        )


def review_manifest(manifest: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    review_routes(manifest, findings)
    review_tables(manifest, findings)
    review_integrations(manifest, findings)
    review_deployment(manifest, findings)
    return sorted(findings, key=lambda item: (SEVERITY_ORDER[item.severity], item.area, item.item))


def summarize(findings: list[Finding]) -> dict[str, Any]:
    counts = {severity: 0 for severity in SEVERITY_ORDER}
    by_area: dict[str, int] = {}
    for finding in findings:
        counts[finding.severity] += 1
        by_area[finding.area] = by_area.get(finding.area, 0) + 1

    if counts["blocker"]:
        decision = "do_not_launch"
    elif counts["high"]:
        decision = "preview_only"
    else:
        decision = "launch_candidate"

    return {
        "decision": decision,
        "finding_count": len(findings),
        "counts_by_severity": counts,
        "counts_by_area": dict(sorted(by_area.items())),
    }


def write_outputs(findings: list[Finding], summary: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "findings.json").open("w") as handle:
        json.dump([asdict(finding) for finding in findings], handle, indent=2)
        handle.write("\n")

    with (out_dir / "release_summary.json").open("w") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")

    with (out_dir / "finding_queue.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["severity", "area", "item", "problem", "recommendation"])
        writer.writeheader()
        for finding in findings:
            writer.writerow(asdict(finding))

    lines = [
        "# Generated App Release Brief",
        "",
        f"Decision: `{summary['decision']}`",
        f"Findings: {summary['finding_count']}",
        "",
        "## Counts By Severity",
        "",
    ]
    for severity, count in summary["counts_by_severity"].items():
        lines.append(f"- {severity}: {count}")
    lines.extend(["", "## Highest Priority Findings", ""])
    for finding in findings[:6]:
        lines.append(f"- **{finding.severity} / {finding.area} / {finding.item}**: {finding.problem} {finding.recommendation}")
    lines.extend(
        [
            "",
            "## Launch Gate",
            "",
            "Keep the app in preview until blocker and high findings are resolved, rerun the gate, and attach the generated finding queue to the handoff.",
            "Use sandbox credentials and synthetic data until the owner approves production access, payment webhooks, and external-message sending.",
        ]
    )
    (out_dir / "release_brief.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Review an AI-generated app manifest before launch.")
    parser.add_argument("--manifest", type=Path, default=Path("input/generated_app_manifest.json"))
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    findings = review_manifest(manifest)
    summary = summarize(findings)
    write_outputs(findings, summary, args.out)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
