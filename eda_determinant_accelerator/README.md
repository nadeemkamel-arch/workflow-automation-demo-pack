# FPGA Determinant Accelerator with ARM64 Golden Model

Public EDA/digital-design work sample for AI training and hardware-oriented contract screening.

This project shows a complete small hardware design loop:

- SystemVerilog RTL for a determinant accelerator.
- Ready/valid row-major input streaming.
- Signed arithmetic with a shared iterative 64-bit divider.
- Fraction-free Bareiss elimination for exact integer determinants.
- C/ARM64 software golden model.
- Verilator C++ simulation harness.
- Directed and randomized verification.
- Yosys synthesis and latency/resource reporting.

## Current Results

| Metric | Result |
| --- | ---: |
| RTL simulation cases | 108/108 pass |
| Supported matrix sizes | 1x1 through 4x4 |
| Input width | signed 16-bit |
| Determinant output | signed 64-bit |
| 1x1 average latency | 3 cycles |
| 2x2 average latency | 6 cycles |
| 3x3 average latency | 359.6 cycles |
| 4x4 average latency | 978.1 cycles |
| Yosys generic cell count | 98,467 |

## Files To Review

- `rtl/det_accel.sv`: top-level accelerator FSM and datapath.
- `rtl/signed_divider.sv`: shared signed restoring divider.
- `rtl/det_pkg.sv`: shared parameters and state definitions.
- `sim/det_accel_tb.cpp`: Verilator testbench and software comparison harness.
- `src/det_arm64.S`: ARM64 determinant golden model.
- `docs/architecture.md`: algorithm, datapath, and state-machine notes.
- `docs/verification.md`: test strategy and current pass result.
- `reports/sim_summary.md`: generated simulation summary.
- `reports/performance_summary.md`: latency and synthesis summary.

## Scope Note

This is a portfolio sample, not a production IP block. It favors clarity, testability, and a complete explainable design flow over throughput optimization.
