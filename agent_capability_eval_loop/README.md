# Agent Capability Eval Loop

Public-safe proof for capability agents that need evals, monitoring, audit trails, and tight user-feedback loops before they are trusted in a real workflow. The sample uses fictional engineering-agent runs and turns raw telemetry into a launch decision, failure-mode queue, and next-iteration tasks.

## What It Produces

- `output/findings.csv`: ranked findings with severity, capability, scenario, area, problem, and recommendation.
- `output/iteration_tasks.json`: dry-run repair tasks for prompt, retrieval, tool, handoff, and monitoring improvements.
- `output/monitoring_summary.json`: pass rates, tool-error rates, audit coverage, feedback counts, and launch decision.
- `output/handoff_brief.md`: owner-readable brief for the next engineering iteration.

## Run

```bash
python3 agent_capability_eval_loop.py --runs input/capability_runs.csv --contract input/eval_contract.json --out output
python3 -m pytest test_agent_capability_eval_loop.py
```

## Why This Matters

Capability agents often look good in demos while failing in the places a production team cares about: missing audit traces, weak retrieval citations, brittle tool calls, unclear fallback behavior, and low-confidence answers that should have handed off to a human. This loop makes those issues visible enough to iterate quickly with domain experts.

## Good First Paid Milestone

1. Pick one capability agent and 15-30 real or redacted scenarios.
2. Define the eval contract: pass-rate threshold, required trace fields, citation expectations, handoff rules, and tool-error limits.
3. Run the eval loop and produce a repair queue with a small monitoring summary.
4. Patch one blocker or high-severity failure mode and leave the check runnable for the next iteration.
