from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

RECORD_COLUMNS = {
    "source_id",
    "client",
    "period",
    "source_type",
    "title",
    "content",
    "sensitivity",
    "approved_tool",
}

REQUEST_COLUMNS = {
    "request_id",
    "client",
    "question",
    "required_source_types",
    "requested_action",
}

ACTION_TOOL = {
    "answer_question": "finance_ops_digest",
    "pay_vendor": "bank_review",
    "create_task": "task_manager",
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "be",
    "can",
    "did",
    "for",
    "if",
    "in",
    "is",
    "it",
    "on",
    "or",
    "should",
    "the",
    "to",
    "we",
    "what",
    "why",
}


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    client: str
    period: str
    source_type: str
    title: str
    content: str
    sensitivity: str
    approved_tool: str


@dataclass(frozen=True)
class OperatorRequest:
    request_id: str
    client: str
    question: str
    required_source_types: list[str]
    requested_action: str


@dataclass(frozen=True)
class ContextPacket:
    request_id: str
    client: str
    question: str
    requested_action: str
    route: str
    next_action: str
    live_action_allowed: bool
    cited_sources: list[dict[str, str]]
    missing_source_types: list[str]
    dry_run_payload: dict[str, object]


def _read_csv(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(required_columns - columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        rows = list(reader)
    if not rows:
        raise ValueError(f"No rows found in {path}")
    return rows


def read_records(path: Path) -> list[SourceRecord]:
    return [SourceRecord(**row) for row in _read_csv(path, RECORD_COLUMNS)]


def read_requests(path: Path) -> list[OperatorRequest]:
    requests = []
    for row in _read_csv(path, REQUEST_COLUMNS):
        requests.append(
            OperatorRequest(
                request_id=row["request_id"],
                client=row["client"],
                question=row["question"],
                required_source_types=[
                    source_type.strip()
                    for source_type in row["required_source_types"].split(";")
                    if source_type.strip()
                ],
                requested_action=row["requested_action"],
            )
        )
    return requests


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOP_WORDS and len(token) > 2
    }


def _score(request: OperatorRequest, record: SourceRecord) -> int:
    if record.client != request.client:
        return -1
    question_tokens = _tokens(request.question)
    record_tokens = _tokens(" ".join([record.title, record.content, record.source_type]))
    overlap = len(question_tokens & record_tokens)
    if overlap == 0:
        return 0
    required_bonus = 3 if record.source_type in request.required_source_types else 0
    return overlap + required_bonus


def retrieve_sources(
    request: OperatorRequest,
    records: list[SourceRecord],
    limit: int = 3,
) -> list[SourceRecord]:
    scored = [
        (score, record)
        for record in records
        if (score := _score(request, record)) >= 0
    ]
    scored.sort(key=lambda item: (-item[0], item[1].source_id))
    positive_records = [record for score, record in scored if score > 0]
    required_matches = [
        record
        for record in positive_records
        if record.source_type in request.required_source_types
    ]
    if required_matches:
        return required_matches[:limit]
    return positive_records[:limit]


def _route(request: OperatorRequest, sources: list[SourceRecord]) -> tuple[str, str, bool]:
    if not sources:
        return "needs_more_context", "ask_for_missing_records", False
    if request.requested_action == "pay_vendor":
        return "restricted_action_review", "review_sources_before_payment_decision", False
    if any(source.sensitivity == "high" for source in sources):
        return "sensitive_context_review", "finance_owner_review_required", False
    return "ready_for_analyst_review", "draft_answer_from_cited_sources", False


def build_context_packet(request: OperatorRequest, sources: list[SourceRecord]) -> ContextPacket:
    found_types = {source.source_type for source in sources}
    missing_types = [
        source_type
        for source_type in request.required_source_types
        if source_type not in found_types
    ]
    route, next_action, live_action_allowed = _route(request, sources)
    tool = ACTION_TOOL.get(request.requested_action, "manual_review")
    cited_sources = [
        {
            "source_id": source.source_id,
            "source_type": source.source_type,
            "title": source.title,
            "sensitivity": source.sensitivity,
            "approved_tool": source.approved_tool,
        }
        for source in sources
    ]
    dry_run_payload = {
        "status": "dry_run_only",
        "tool": tool,
        "client": request.client,
        "request_id": request.request_id,
        "requested_action": request.requested_action,
        "source_ids": [source.source_id for source in sources],
        "requires_owner_approval": True,
    }
    return ContextPacket(
        request_id=request.request_id,
        client=request.client,
        question=request.question,
        requested_action=request.requested_action,
        route=route,
        next_action=next_action,
        live_action_allowed=live_action_allowed,
        cited_sources=cited_sources,
        missing_source_types=missing_types,
        dry_run_payload=dry_run_payload,
    )


def build_packets(records_path: Path, requests_path: Path) -> list[ContextPacket]:
    records = read_records(records_path)
    requests = read_requests(requests_path)
    return [
        build_context_packet(request, retrieve_sources(request, records))
        for request in requests
    ]


def _count(packets: list[ContextPacket], field_name: str) -> dict[str, int]:
    return dict(Counter(str(getattr(packet, field_name)) for packet in packets))


def render_digest(packets: list[ContextPacket]) -> str:
    lines = [
        "# Startup Finance Context Digest",
        "",
        "Fictional sample output. All accounting, payment, task, and customer-facing actions are dry-run only.",
        "",
        "| Request | Route | Action | Sources | Missing |",
        "| --- | --- | --- | --- | --- |",
    ]
    for packet in packets:
        source_ids = ", ".join(source["source_id"] for source in packet.cited_sources) or "-"
        missing = ", ".join(packet.missing_source_types) or "-"
        lines.append(
            f"| {packet.request_id} | {packet.route} | {packet.next_action} | {source_ids} | {missing} |"
        )
    lines.extend(
        [
            "",
            "## Launch Gate",
            "",
            "- No payment release without owner approval and source review.",
            "- No accounting-system write until dry-run payloads are inspected.",
            "- Keep sensitive payroll and bank context out of public logs.",
            "- Require cited sources before drafting a client or founder-facing answer.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(packets: list[ContextPacket], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    serialized = [asdict(packet) for packet in packets]
    (out_dir / "context_packets.json").write_text(json.dumps(serialized, indent=2) + "\n", encoding="utf-8")

    with (out_dir / "action_queue.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "request_id",
                "client",
                "requested_action",
                "route",
                "next_action",
                "live_action_allowed",
                "tool",
                "source_ids",
            ],
        )
        writer.writeheader()
        for packet in packets:
            writer.writerow(
                {
                    "request_id": packet.request_id,
                    "client": packet.client,
                    "requested_action": packet.requested_action,
                    "route": packet.route,
                    "next_action": packet.next_action,
                    "live_action_allowed": str(packet.live_action_allowed).lower(),
                    "tool": packet.dry_run_payload["tool"],
                    "source_ids": ";".join(packet.dry_run_payload["source_ids"]),
                }
            )

    (out_dir / "finance_ops_digest.md").write_text(render_digest(packets), encoding="utf-8")
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "request_count": len(packets),
                "route_counts": _count(packets, "route"),
                "action_counts": _count(packets, "requested_action"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build dry-run finance context packets.")
    parser.add_argument("--records", type=Path, default=Path("input/source_records.csv"))
    parser.add_argument("--requests", type=Path, default=Path("input/operator_requests.csv"))
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()

    packets = build_packets(args.records, args.requests)
    write_outputs(packets, args.out)


if __name__ == "__main__":
    main()
