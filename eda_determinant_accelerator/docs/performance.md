# Performance

## Simulation Latency

Measured by the Verilator harness from transaction start to `out_valid`.

| n | Cases | Min cycles | Max cycles | Average cycles |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 26 | 3 | 3 | 3.0 |
| 2 | 27 | 6 | 6 | 6.0 |
| 3 | 28 | 358 | 368 | 359.6 |
| 4 | 27 | 977 | 983 | 978.1 |

## Synthesis Snapshot

Yosys generic synthesis currently reports:

| Metric | Count |
| --- | ---: |
| Wires | 7,678 |
| Wire bits | 163,581 |
| Cells | 98,467 |

The high generic cell count is driven by 64-bit signed multiplication, 64-bit matrix storage, and the generic gate-level mapping used by the open-source flow. A board-specific FPGA flow would map parts of this design into LUTs, carry chains, flip-flops, and possibly DSP blocks.

## Interpretation

The design is latency-heavy but conceptually clean. The single iterative divider takes many cycles, and Bareiss elimination performs several divisions for `3x3` and `4x4` matrices. This is a good first portfolio implementation because it exposes clear tradeoffs:

- Reuse one divider to save area.
- Accept higher latency for easier verification.
- Keep exact integer arithmetic instead of using approximate floating-point arithmetic.

## Future Optimization Ideas

- Add a pipelined divider.
- Reuse or pipeline multipliers more deliberately.
- Add a fixed-point or floating-point mode.
- Add a block RAM based matrix store for larger `MAX_N`.
- Add board-specific timing reports from Vivado or Quartus.
