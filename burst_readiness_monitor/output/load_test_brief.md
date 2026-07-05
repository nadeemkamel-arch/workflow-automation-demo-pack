# Burst Readiness Brief

Fictional sample output for a limited-beta platform preparing for a traffic burst.
Alert, scaling, and rollback actions are dry-run only until a client approves live routing.

- Target burst: 500 RPS
- Observed synthetic peak: 545.0 RPS
- Target met in sample: yes

| Endpoint | Severity | Peak RPS | p95 ms | 5xx rate | Cost / 1k | Route | Owner |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| artist_dashboard | warning | 45.00 | 350 | 0.0011 | $0.096 | capacity_plan | creator_tools |
| event_discovery | warning | 130.00 | 420 | 0.0012 | $0.079 | capacity_plan | product |
| homepage | ok | 150.00 | 210 | 0.0004 | $0.036 | ready | frontend |
| media_upload | critical | 60.00 | 960 | 0.0050 | $0.306 | launch_blocker | platform |
| notifications | warning | 40.00 | 500 | 0.0008 | $0.083 | capacity_plan | platform |
| ticket_waitlist | critical | 120.00 | 810 | 0.0172 | $0.131 | launch_blocker | growth |

## Launch Gates

- Fix critical endpoint errors or database saturation before promoting traffic.
- Keep autoscale, cache, and queue changes behind a reversible rollout plan.
- Add owner-visible alerts for p95 latency, 5xx rate, worker backlog, and spend per 1k requests.
- Load test again after changes and compare endpoint-level p95, p99, 5xx rate, and cost.
- Do not connect production credentials or live customer messaging until sample checks pass.
