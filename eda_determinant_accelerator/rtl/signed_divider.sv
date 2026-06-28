module signed_divider #(
  parameter int WIDTH = 64
) (
  input  logic clk,
  input  logic rst_n,
  input  logic start,
  input  logic signed [WIDTH-1:0] dividend,
  input  logic signed [WIDTH-1:0] divisor,
  output logic busy,
  output logic valid,
  output logic signed [WIDTH-1:0] quotient,
  output logic divide_by_zero
);
  logic result_negative;
  logic [WIDTH-1:0] dividend_abs;
  logic [WIDTH-1:0] divisor_abs;
  logic [WIDTH-1:0] quotient_work;
  logic [WIDTH:0] remainder;
  logic [$clog2(WIDTH)-1:0] bit_index;

  logic [WIDTH:0] remainder_shifted;
  logic [WIDTH:0] remainder_next;
  logic [WIDTH-1:0] quotient_next;

  function automatic logic [WIDTH-1:0] abs_signed(input logic signed [WIDTH-1:0] value);
    abs_signed = value[WIDTH-1] ? (~value + {{(WIDTH-1){1'b0}}, 1'b1}) : value;
  endfunction

  always_comb begin
    remainder_shifted = {remainder[WIDTH-1:0], dividend_abs[bit_index]};
    remainder_next = remainder_shifted;
    quotient_next = quotient_work;

    if (divisor_abs != '0 && remainder_shifted >= {1'b0, divisor_abs}) begin
      remainder_next = remainder_shifted - {1'b0, divisor_abs};
      quotient_next[bit_index] = 1'b1;
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      busy <= 1'b0;
      valid <= 1'b0;
      quotient <= '0;
      divide_by_zero <= 1'b0;
      result_negative <= 1'b0;
      dividend_abs <= '0;
      divisor_abs <= '0;
      quotient_work <= '0;
      remainder <= '0;
      bit_index <= '0;
    end else begin
      valid <= 1'b0;
      divide_by_zero <= 1'b0;

      if (start && !busy) begin
        if (divisor == '0) begin
          quotient <= '0;
          valid <= 1'b1;
          divide_by_zero <= 1'b1;
        end else begin
          busy <= 1'b1;
          result_negative <= dividend[WIDTH-1] ^ divisor[WIDTH-1];
          dividend_abs <= abs_signed(dividend);
          divisor_abs <= abs_signed(divisor);
          quotient_work <= '0;
          remainder <= '0;
          bit_index <= WIDTH - 1;
        end
      end else if (busy) begin
        quotient_work <= quotient_next;
        remainder <= remainder_next;

        if (bit_index == '0) begin
          busy <= 1'b0;
          valid <= 1'b1;
          quotient <= result_negative ? -signed'(quotient_next) : signed'(quotient_next);
        end else begin
          bit_index <= bit_index - 1'b1;
        end
      end
    end
  end
endmodule
