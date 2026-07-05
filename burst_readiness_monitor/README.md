# Burst Readiness Monitor

Public-safe load-test and monitoring demo for a limited-beta platform preparing for a traffic burst. The example uses fictional traffic windows for an electronic-music/event platform, but the pattern is meant for any web app that needs to scale carefully without runaway cost or silent failure.

## What It Produces

- `output/endpoint_readiness.csv`: endpoint-level p95, p99, 5xx rate, cost per 1k requests, owner route, and severity.
- `output/alert_payloads.json`: dry-run alert payloads with idempotency keys for non-ready endpoints.
- `output/load_test_brief.md`: owner-readable load-test brief with launch gates.
- `output/run_summary.json`: peak RPS, target status, route counts, and owner counts.

## Run

```bash
python3 burst_readiness_monitor.py --input input/traffic_windows.csv --out output --target-rps 500
python3 -m pytest test_burst_readiness_monitor.py
```

## Client Handoff Notes

Good first milestone:

- Confirm the critical user flows and target burst, such as 500 RPS for launch windows.
- Run a short load test against staging or a read-only production-like path.
- Add owner-visible alerts for p95 latency, 5xx rate, worker backlog, and spend per 1k requests.
- Keep autoscale, cache, queue, and rollback changes behind a reversible rollout plan.
- Re-test after the first fix pass before enabling live alerts or production credentials.
