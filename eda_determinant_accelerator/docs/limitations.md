# Limitations

- The RTL accelerator supports only `1x1` through `4x4` matrices.
- RTL input width is signed 16-bit.
- RTL output and intermediates are signed 64-bit.
- Overflow detection is not implemented.
- The current RTL is optimized for clarity and verification, not throughput.
- The synthesis report is generic Yosys synthesis, not board-specific place-and-route.
- No physical FPGA board is required yet; this version is simulation and synthesis focused.

## Hardware Extensions

Good next hardware paths:

- Digilent Basys 3 with Vivado, switches/buttons, LEDs, and seven-segment output.
- Terasic DE10-Lite with Quartus and MAX 10 FPGA flow.
- Memory-mapped accelerator connected to a simple bus or soft CPU.

## Software Extensions

- Add a CSV or file-input mode.
- Add overflow checks in the C/ARM64 reference path.
- Add performance timing for the software model and compare against simulated RTL cycles.
