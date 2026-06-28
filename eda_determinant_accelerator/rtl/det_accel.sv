module det_accel #(
  parameter int MAX_N = det_pkg::DET_MAX_N,
  parameter int DATA_W = det_pkg::DET_DATA_W,
  parameter int ACC_W = det_pkg::DET_ACC_W
) (
  input  logic clk,
  input  logic rst_n,
  input  logic start,
  input  logic [2:0] n,
  input  logic in_valid,
  input  logic signed [DATA_W-1:0] in_data,
  output logic in_ready,
  output logic busy,
  output logic out_valid,
  input  logic out_ready,
  output logic signed [ACC_W-1:0] det,
  output logic error
);
  localparam int ELEMENTS = MAX_N * MAX_N;
  localparam int ADDR_W = $clog2(ELEMENTS);
  localparam int COUNT_W = $clog2(ELEMENTS + 1);
  localparam logic [3:0] ST_IDLE = 4'd0;
  localparam logic [3:0] ST_LOAD = 4'd1;
  localparam logic [3:0] ST_BASE = 4'd2;
  localparam logic [3:0] ST_PIVOT = 4'd3;
  localparam logic [3:0] ST_FIND_SWAP = 4'd4;
  localparam logic [3:0] ST_SWAP = 4'd5;
  localparam logic [3:0] ST_ROW_SETUP = 4'd6;
  localparam logic [3:0] ST_COL_SETUP = 4'd7;
  localparam logic [3:0] ST_DIV_START = 4'd8;
  localparam logic [3:0] ST_DIV_WAIT = 4'd9;
  localparam logic [3:0] ST_ADVANCE = 4'd10;
  localparam logic [3:0] ST_DONE = 4'd11;

  logic [3:0] state;

  logic signed [ACC_W-1:0] mem [0:ELEMENTS-1];
  logic [2:0] latched_n;
  logic [COUNT_W-1:0] load_count;
  logic [COUNT_W-1:0] total_count;

  logic [2:0] k;
  logic [2:0] i;
  logic [2:0] j;
  logic [2:0] swap_row;
  logic [2:0] swap_col;

  logic signed [ACC_W-1:0] sign;
  logic signed [ACC_W-1:0] previous_pivot;
  logic signed [ACC_W-1:0] pivot;
  logic signed [ACC_W-1:0] aik;
  logic signed [ACC_W-1:0] numerator;
  logic signed [ACC_W-1:0] det_q;
  logic error_q;

  logic [ADDR_W-1:0] target_addr;
  logic div_start;
  logic div_busy;
  logic div_valid;
  logic div_error;
  logic signed [ACC_W-1:0] div_quotient;

  function automatic logic [ADDR_W-1:0] addr(input logic [2:0] row, input logic [2:0] col);
    addr = (row * latched_n) + col;
  endfunction

  signed_divider #(
    .WIDTH(ACC_W)
  ) divider (
    .clk(clk),
    .rst_n(rst_n),
    .start(div_start),
    .dividend(numerator),
    .divisor(previous_pivot),
    .busy(div_busy),
    .valid(div_valid),
    .quotient(div_quotient),
    .divide_by_zero(div_error)
  );

  assign in_ready = (state == ST_LOAD);
  assign busy = (state != ST_IDLE);
  assign out_valid = (state == ST_DONE);
  assign det = det_q;
  assign error = error_q;
  assign div_start = (state == ST_DIV_START) && !div_busy;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= ST_IDLE;
      latched_n <= '0;
      load_count <= '0;
      total_count <= '0;
      k <= '0;
      i <= '0;
      j <= '0;
      swap_row <= '0;
      swap_col <= '0;
      sign <= 64'sd1;
      previous_pivot <= 64'sd1;
      pivot <= '0;
      aik <= '0;
      numerator <= '0;
      target_addr <= '0;
      det_q <= '0;
      error_q <= 1'b0;
    end else begin
      case (state)
        ST_IDLE: begin
          error_q <= 1'b0;
          det_q <= '0;
          if (start) begin
            if (n < 3'd1 || n > MAX_N) begin
              error_q <= 1'b1;
              state <= ST_DONE;
            end else begin
              latched_n <= n;
              total_count <= n * n;
              load_count <= '0;
              sign <= 64'sd1;
              previous_pivot <= 64'sd1;
              state <= ST_LOAD;
            end
          end
        end

        ST_LOAD: begin
          if (in_valid && in_ready) begin
            mem[load_count[ADDR_W-1:0]] <= {{(ACC_W-DATA_W){in_data[DATA_W-1]}}, in_data};
            load_count <= load_count + 1'b1;
            if ((load_count + 1'b1) == total_count) begin
              state <= ST_BASE;
            end
          end
        end

        ST_BASE: begin
          if (latched_n == 3'd1) begin
            det_q <= mem[0];
            state <= ST_DONE;
          end else if (latched_n == 3'd2) begin
            det_q <= (mem[0] * mem[3]) - (mem[1] * mem[2]);
            state <= ST_DONE;
          end else begin
            k <= '0;
            previous_pivot <= 64'sd1;
            sign <= 64'sd1;
            state <= ST_PIVOT;
          end
        end

        ST_PIVOT: begin
          if (mem[addr(k, k)] != '0) begin
            pivot <= mem[addr(k, k)];
            i <= k + 1'b1;
            state <= ST_ROW_SETUP;
          end else begin
            swap_row <= k + 1'b1;
            state <= ST_FIND_SWAP;
          end
        end

        ST_FIND_SWAP: begin
          if (swap_row >= latched_n) begin
            det_q <= '0;
            state <= ST_DONE;
          end else if (mem[addr(swap_row, k)] != '0) begin
            swap_col <= '0;
            state <= ST_SWAP;
          end else begin
            swap_row <= swap_row + 1'b1;
          end
        end

        ST_SWAP: begin
          mem[addr(k, swap_col)] <= mem[addr(swap_row, swap_col)];
          mem[addr(swap_row, swap_col)] <= mem[addr(k, swap_col)];

          if ((swap_col + 1'b1) >= latched_n) begin
            sign <= -sign;
            state <= ST_PIVOT;
          end else begin
            swap_col <= swap_col + 1'b1;
          end
        end

        ST_ROW_SETUP: begin
          if (i >= latched_n) begin
            state <= ST_ADVANCE;
          end else begin
            aik <= mem[addr(i, k)];
            j <= k + 1'b1;
            state <= ST_COL_SETUP;
          end
        end

        ST_COL_SETUP: begin
          if (j >= latched_n) begin
            i <= i + 1'b1;
            state <= ST_ROW_SETUP;
          end else begin
            numerator <= (mem[addr(i, j)] * pivot) - (aik * mem[addr(k, j)]);
            target_addr <= addr(i, j);
            state <= ST_DIV_START;
          end
        end

        ST_DIV_START: begin
          if (!div_busy) begin
            state <= ST_DIV_WAIT;
          end
        end

        ST_DIV_WAIT: begin
          if (div_valid) begin
            if (div_error) begin
              error_q <= 1'b1;
              det_q <= '0;
              state <= ST_DONE;
            end else begin
              mem[target_addr] <= div_quotient;
              j <= j + 1'b1;
              state <= ST_COL_SETUP;
            end
          end
        end

        ST_ADVANCE: begin
          previous_pivot <= pivot;
          if ((k + 1'b1) >= (latched_n - 1'b1)) begin
            det_q <= mem[addr(latched_n - 1'b1, latched_n - 1'b1)] * sign;
            state <= ST_DONE;
          end else begin
            k <= k + 1'b1;
            state <= ST_PIVOT;
          end
        end

        ST_DONE: begin
          if (out_ready) begin
            state <= ST_IDLE;
          end
        end

        default: begin
          error_q <= 1'b1;
          det_q <= '0;
          state <= ST_DONE;
        end
      endcase
    end
  end
endmodule
