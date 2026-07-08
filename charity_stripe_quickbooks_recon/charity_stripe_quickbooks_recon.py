from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AccountRule:
    charity_code: str
    currency: str
    donation_income_account: str
    fee_expense_account: str
    clearing_account: str
    quickbooks_class: str


@dataclass(frozen=True)
class ReconciliationRow:
    payout_id: str
    transaction_id: str
    charity_code: str
    donor_label: str
    currency: str
    gross_amount: str
    fee_amount: str
    net_amount: str
    donation_income_account: str
    fee_expense_account: str
    clearing_account: str
    quickbooks_class: str
    review_status: str


@dataclass(frozen=True)
class JournalLine:
    payout_id: str
    transaction_id: str
    line_type: str
    account: str
    quickbooks_class: str
    debit: str
    credit: str
    memo: str


@dataclass(frozen=True)
class ExceptionItem:
    payout_id: str
    transaction_id: str
    severity: str
    code: str
    message: str
    recommended_action: str


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _money(cents: int) -> str:
    return f"{Decimal(cents) / Decimal(100):.2f}"


def _rule_key(charity_code: str, currency: str) -> tuple[str, str]:
    return charity_code.strip().upper(), currency.strip().upper()


def read_rules(path: Path) -> dict[tuple[str, str], AccountRule]:
    payload = _load_json(path)
    rules = {}
    for row in payload.get("rules", []):
        rule = AccountRule(**row)
        rules[_rule_key(rule.charity_code, rule.currency)] = rule
    if not rules:
        raise ValueError("No account rules found")
    return rules


def _transaction_net(transaction: dict[str, Any]) -> int:
    return int(transaction["gross_amount_cents"]) - int(transaction["fee_amount_cents"])


def _append_journal_lines(
    journal_lines: list[JournalLine],
    payout_id: str,
    transaction: dict[str, Any],
    rule: AccountRule,
) -> None:
    transaction_id = transaction["balance_transaction_id"]
    gross = int(transaction["gross_amount_cents"])
    fee = int(transaction["fee_amount_cents"])
    donor_label = transaction["donor_label"]
    charity_code = transaction["charity_code"]
    memo_prefix = f"{donor_label} / {charity_code} / {transaction_id}"

    journal_lines.extend(
        [
            JournalLine(
                payout_id=payout_id,
                transaction_id=transaction_id,
                line_type="gross_donation_to_clearing",
                account=rule.clearing_account,
                quickbooks_class=rule.quickbooks_class,
                debit=_money(gross),
                credit="0",
                memo=f"{memo_prefix}: gross donation held in Stripe clearing",
            ),
            JournalLine(
                payout_id=payout_id,
                transaction_id=transaction_id,
                line_type="donation_income",
                account=rule.donation_income_account,
                quickbooks_class=rule.quickbooks_class,
                debit="0",
                credit=_money(gross),
                memo=f"{memo_prefix}: donation income classification",
            ),
            JournalLine(
                payout_id=payout_id,
                transaction_id=transaction_id,
                line_type="stripe_fee_expense",
                account=rule.fee_expense_account,
                quickbooks_class=rule.quickbooks_class,
                debit=_money(fee),
                credit="0",
                memo=f"{memo_prefix}: Stripe processing fee",
            ),
            JournalLine(
                payout_id=payout_id,
                transaction_id=transaction_id,
                line_type="fee_reduces_clearing",
                account=rule.clearing_account,
                quickbooks_class=rule.quickbooks_class,
                debit="0",
                credit=_money(fee),
                memo=f"{memo_prefix}: fee netted out of Stripe clearing",
            ),
        ]
    )


def reconcile(
    payouts_payload: dict[str, Any],
    rules: dict[tuple[str, str], AccountRule],
) -> tuple[list[ReconciliationRow], list[JournalLine], list[ExceptionItem], dict[str, Any]]:
    reconciliation_rows: list[ReconciliationRow] = []
    journal_lines: list[JournalLine] = []
    exceptions: list[ExceptionItem] = []
    totals_by_payout: dict[str, dict[str, int]] = {}

    for payout in payouts_payload.get("payouts", []):
        payout_id = payout["payout_id"]
        payout_currency = payout["currency"].upper()
        transactions = payout.get("transactions", [])
        expected_net = int(payout["net_amount_cents"])
        computed_net = sum(_transaction_net(transaction) for transaction in transactions)
        totals_by_payout[payout_id] = {
            "expected_net_amount_cents": expected_net,
            "computed_net_amount_cents": computed_net,
            "delta_cents": computed_net - expected_net,
        }
        if computed_net != expected_net:
            exceptions.append(
                ExceptionItem(
                    payout_id=payout_id,
                    transaction_id="-",
                    severity="high",
                    code="payout_net_mismatch",
                    message=(
                        f"Computed transaction net {_money(computed_net)} does not match "
                        f"payout net {_money(expected_net)}."
                    ),
                    recommended_action="Review Stripe payout export for missing refunds, disputes, adjustments, or excluded balance transactions.",
                )
            )

        for transaction in transactions:
            transaction_id = transaction["balance_transaction_id"]
            status = transaction.get("status", "").lower()
            transaction_currency = transaction["currency"].upper()
            rule = rules.get(_rule_key(transaction["charity_code"], transaction_currency))
            review_status = "ready_for_bookkeeper_review"

            if transaction_currency != payout_currency:
                review_status = "blocked_currency_review"
                exceptions.append(
                    ExceptionItem(
                        payout_id=payout_id,
                        transaction_id=transaction_id,
                        severity="high",
                        code="currency_mismatch",
                        message=f"Transaction currency {transaction_currency} differs from payout currency {payout_currency}.",
                        recommended_action="Confirm whether QuickBooks needs a separate currency conversion or clearing account.",
                    )
                )

            if status != "available":
                review_status = "blocked_not_available"
                exceptions.append(
                    ExceptionItem(
                        payout_id=payout_id,
                        transaction_id=transaction_id,
                        severity="medium",
                        code="transaction_not_available",
                        message=f"Transaction status is {status or 'blank'}, not available.",
                        recommended_action="Wait for Stripe settlement or export a newer payout snapshot.",
                    )
                )

            if rule is None:
                review_status = "blocked_missing_account_rule"
                exceptions.append(
                    ExceptionItem(
                        payout_id=payout_id,
                        transaction_id=transaction_id,
                        severity="high",
                        code="missing_account_rule",
                        message=(
                            f"No account rule for charity {transaction['charity_code']} "
                            f"in {transaction_currency}."
                        ),
                        recommended_action="Add a bookkeeper-approved donation income, fee expense, clearing account, and class mapping.",
                    )
                )
                reconciliation_rows.append(
                    ReconciliationRow(
                        payout_id=payout_id,
                        transaction_id=transaction_id,
                        charity_code=transaction["charity_code"],
                        donor_label=transaction["donor_label"],
                        currency=transaction_currency,
                        gross_amount=_money(int(transaction["gross_amount_cents"])),
                        fee_amount=_money(int(transaction["fee_amount_cents"])),
                        net_amount=_money(_transaction_net(transaction)),
                        donation_income_account="",
                        fee_expense_account="",
                        clearing_account="",
                        quickbooks_class="",
                        review_status=review_status,
                    )
                )
                continue

            reconciliation_rows.append(
                ReconciliationRow(
                    payout_id=payout_id,
                    transaction_id=transaction_id,
                    charity_code=transaction["charity_code"],
                    donor_label=transaction["donor_label"],
                    currency=transaction_currency,
                    gross_amount=_money(int(transaction["gross_amount_cents"])),
                    fee_amount=_money(int(transaction["fee_amount_cents"])),
                    net_amount=_money(_transaction_net(transaction)),
                    donation_income_account=rule.donation_income_account,
                    fee_expense_account=rule.fee_expense_account,
                    clearing_account=rule.clearing_account,
                    quickbooks_class=rule.quickbooks_class,
                    review_status=review_status,
                )
            )
            if review_status == "ready_for_bookkeeper_review":
                _append_journal_lines(journal_lines, payout_id, transaction, rule)

    summary = {
        "organization": payouts_payload.get("organization", "unknown"),
        "snapshot_date": payouts_payload.get("snapshot_date", "unknown"),
        "payout_count": len(payouts_payload.get("payouts", [])),
        "transaction_count": sum(len(payout.get("transactions", [])) for payout in payouts_payload.get("payouts", [])),
        "reconciliation_row_count": len(reconciliation_rows),
        "journal_line_count": len(journal_lines),
        "exception_count": len(exceptions),
        "exceptions_by_code": dict(Counter(exception.code for exception in exceptions)),
        "totals_by_payout": totals_by_payout,
        "live_writes_allowed": False,
        "launch_decision": "review_required" if exceptions else "ready_for_accounting_review",
    }
    return reconciliation_rows, journal_lines, exceptions, summary


def _write_csv(path: Path, rows: list[Any], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _journal_balance_by_payout(journal_lines: list[JournalLine]) -> dict[str, dict[str, str]]:
    totals: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"debit": Decimal("0"), "credit": Decimal("0")})
    for line in journal_lines:
        totals[line.payout_id]["debit"] += Decimal(line.debit)
        totals[line.payout_id]["credit"] += Decimal(line.credit)
    return {
        payout_id: {
            "debit": f"{values['debit']:.2f}",
            "credit": f"{values['credit']:.2f}",
            "balanced": str(values["debit"] == values["credit"]),
        }
        for payout_id, values in sorted(totals.items())
    }


def render_handoff(summary: dict[str, Any], exceptions: list[ExceptionItem], journal_lines: list[JournalLine]) -> str:
    lines = [
        "# Stripe to QuickBooks Reconciliation Handoff",
        "",
        "Fictional sample output. This is a dry-run packet for owner/bookkeeper review, not accounting advice and not a live QuickBooks write.",
        "",
        f"- Organization: {summary['organization']}",
        f"- Snapshot date: {summary['snapshot_date']}",
        f"- Payouts reviewed: {summary['payout_count']}",
        f"- Transactions reviewed: {summary['transaction_count']}",
        f"- Journal preview lines: {summary['journal_line_count']}",
        f"- Exceptions: {summary['exception_count']}",
        f"- Launch decision: {summary['launch_decision']}",
        "",
        "## Journal Balance Check",
        "",
    ]
    balances = _journal_balance_by_payout(journal_lines)
    if balances:
        lines.append("| Payout | Debit | Credit | Balanced |")
        lines.append("| --- | ---: | ---: | --- |")
        for payout_id, values in balances.items():
            lines.append(f"| {payout_id} | {values['debit']} | {values['credit']} | {values['balanced']} |")
    else:
        lines.append("No journal preview lines were generated.")

    lines.extend(["", "## Review Queue", ""])
    if exceptions:
        for item in exceptions:
            lines.append(f"- `{item.code}` on `{item.payout_id}` / `{item.transaction_id}`: {item.message}")
    else:
        lines.append("- No exceptions detected in the sample snapshot.")

    lines.extend(
        [
            "",
            "## Owner Gate",
            "",
            "- Confirm each QuickBooks account and class mapping with the bookkeeper before import.",
            "- Confirm how existing Stripe deposits are represented in QuickBooks before creating journal entries.",
            "- Keep API keys, donor names, and account IDs out of public logs.",
            "- Run against a sandbox or exported CSV first; no live writes are enabled in this proof.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(
    reconciliation_rows: list[ReconciliationRow],
    journal_lines: list[JournalLine],
    exceptions: list[ExceptionItem],
    summary: dict[str, Any],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "reconciliation_rows.csv", reconciliation_rows, list(ReconciliationRow.__annotations__))
    _write_csv(out_dir / "journal_preview.csv", journal_lines, list(JournalLine.__annotations__))
    with (out_dir / "exceptions.json").open("w", encoding="utf-8") as handle:
        json.dump([asdict(exception) for exception in exceptions], handle, indent=2)
    with (out_dir / "run_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    (out_dir / "handoff_note.md").write_text(render_handoff(summary, exceptions, journal_lines), encoding="utf-8")


def run(payouts_path: Path, rules_path: Path, out_dir: Path) -> dict[str, Any]:
    payouts_payload = _load_json(payouts_path)
    rules = read_rules(rules_path)
    reconciliation_rows, journal_lines, exceptions, summary = reconcile(payouts_payload, rules)
    write_outputs(reconciliation_rows, journal_lines, exceptions, summary, out_dir)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a dry-run Stripe payout to QuickBooks reconciliation packet.")
    parser.add_argument("--payouts", type=Path, required=True)
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()

    summary = run(args.payouts, args.rules, args.out)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
