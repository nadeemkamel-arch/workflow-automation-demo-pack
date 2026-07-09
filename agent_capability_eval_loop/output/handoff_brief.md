# Agent Capability Eval Handoff

Decision: `block_pilot`
Runs reviewed: 9
Pass rate: 56%
Tool error rate: 11%
Trace coverage: 56%

## Top Findings
- [blocker] qa_report_writer/QA-002: Missing required trace fields: retrieval_set. Recommendation: Add structured trace fields before this capability is used for production decisions.
- [blocker] requirements_retrieval/REQ-002: Missing required trace fields: retrieval_set. Recommendation: Add structured trace fields before this capability is used for production decisions.
- [blocker] requirements_retrieval/REQ-003: Missing required trace fields: tool_status. Recommendation: Add structured trace fields before this capability is used for production decisions.
- [blocker] simulation_orchestration/SIM-002: Missing required trace fields: fallback_path. Recommendation: Add structured trace fields before this capability is used for production decisions.
- [high] qa_report_writer/QA-002: Expected `hands off for human review` but observed `buries contradiction`. Recommendation: Add this scenario to the regression set and patch prompt, retrieval, or tool routing before expansion.
- [high] qa_report_writer/QA-002: Citation coverage 62% is below required 90%. Recommendation: Require source IDs, quoted spans, or document offsets before presenting the answer as grounded.
- [high] qa_report_writer/capability-rollup: Pass rate 67% is below required 80%. Recommendation: Pause expansion and run a targeted repair sprint against failed and borderline scenarios.
- [high] requirements_retrieval/REQ-002: Expected `returns latest revision with source` but observed `returns outdated revision`. Recommendation: Add this scenario to the regression set and patch prompt, retrieval, or tool routing before expansion.

## Next Iteration Tasks
- ITER-d112353a37 (instrumentation): Add structured trace fields before this capability is used for production decisions.
- ITER-e7c21f7b15 (instrumentation): Add structured trace fields before this capability is used for production decisions.
- ITER-d34ba3be7f (instrumentation): Add structured trace fields before this capability is used for production decisions.
- ITER-1361f7ceab (instrumentation): Add structured trace fields before this capability is used for production decisions.
- ITER-03beca0e48 (eval_regression): Add this scenario to the regression set and patch prompt, retrieval, or tool routing before expansion.
- ITER-9426a57a01 (retrieval): Require source IDs, quoted spans, or document offsets before presenting the answer as grounded.
- ITER-646ce31249 (repair_sprint): Pause expansion and run a targeted repair sprint against failed and borderline scenarios.
- ITER-a417af7115 (eval_regression): Add this scenario to the regression set and patch prompt, retrieval, or tool routing before expansion.
