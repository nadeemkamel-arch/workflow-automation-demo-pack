from __future__ import annotations

import json
import subprocess
from pathlib import Path


DEMO_DIR = Path(__file__).parent


def load_workflow() -> dict:
    return json.loads((DEMO_DIR / "workflow.json").read_text())


def test_workflow_has_expected_nodes_and_connections() -> None:
    workflow = load_workflow()
    nodes = {node["name"]: node for node in workflow["nodes"]}

    assert nodes["Webhook: Inbound Requests"]["type"] == "n8n-nodes-base.webhook"
    assert nodes["Code: Score Requests"]["type"] == "n8n-nodes-base.code"
    assert nodes["Respond: Reviewed Action Plan"]["type"] == "n8n-nodes-base.respondToWebhook"
    assert workflow["connections"]["Webhook: Inbound Requests"]["main"][0][0]["node"] == "Code: Score Requests"
    assert workflow["connections"]["Code: Score Requests"]["main"][0][0]["node"] == "Respond: Reviewed Action Plan"


def test_code_node_scores_sample_payload() -> None:
    workflow = load_workflow()
    code_node = next(node for node in workflow["nodes"] if node["name"] == "Code: Score Requests")
    js_code = code_node["parameters"]["jsCode"]
    payload = json.loads((DEMO_DIR / "sample_webhook_payload.json").read_text())
    expected = json.loads((DEMO_DIR / "sample_response.json").read_text())

    runner = f"""
const payload = {json.dumps(payload)};
const items = [{{json: payload}}];
const fn = new Function('items', {json.dumps(js_code)});
const result = fn(items);
console.log(JSON.stringify(result[0].json));
"""
    completed = subprocess.run(
        ["node", "-e", runner],
        check=True,
        capture_output=True,
        text=True,
    )
    actual = json.loads(completed.stdout)

    assert actual["summary"] == expected["summary"]
    assert actual["action_plan"] == expected["action_plan"]
    assert len(actual["triaged_requests"]) == 6
    assert {row["priority"] for row in actual["triaged_requests"]} == {
        "high",
        "review_first",
        "do_not_pursue",
    }
