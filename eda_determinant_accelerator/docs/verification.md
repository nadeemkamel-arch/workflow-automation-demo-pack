# Verification

## Strategy

The RTL is verified with Verilator using a C++ test harness. The harness drives the ready/valid interface, computes expected determinants with a software Bareiss model, compares every RTL result, and emits both human-readable and machine-readable reports.

Generated files:

- `reports/sim_summary.md`
- `reports/latency.csv`
- `reports/waves/det_accel.vcd`

## Directed Tests

| Case | Purpose |
| --- | --- |
| `1x1 scalar` | Base case |
| `2x2 fast path` | Direct determinant equation |
| `2x2 negative` | Signed arithmetic |
| `3x3 normal` | General Bareiss path |
| `3x3 singular` | Zero determinant |
| `3x3 pivot swap` | Row swap and sign handling |
| `4x4 identity` | Stable diagonal matrix |
| `4x4 triangular` | Determinant equals diagonal product |

## Randomized Tests

- 25 random matrices per size from `1x1` through `4x4`.
- Values are generated in a small signed range to avoid overflowing the 64-bit accumulator.
- Every random result is compared against the software model.

## Current Result

`make sim` currently passes:

```text
108/108 RTL simulation cases passed.
```

## Waveform Review

The VCD trace at `reports/waves/det_accel.vcd` can be opened in a waveform viewer such as GTKWave. Signals to inspect first:

- `state`
- `start`
- `in_valid`
- `in_ready`
- `out_valid`
- `det`
- `pivot`
- `previous_pivot`
- divider `busy` and `valid`
