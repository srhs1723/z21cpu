// Z21 ALU for the Z+ 12-bit fantasy CPU.
// Operations wrap to 12 bits, matching the small-machine feel.
module alu(
    input  [3:0]  op,
    input  [11:0] a,
    input  [11:0] b,
    output reg [11:0] y,
    output reg carry,
    output zero,
    output neg
);
    reg [12:0] wide;

    always @* begin
        y = 12'h000;
        carry = 1'b0;
        wide = 13'h0000;

        case (op)
            4'h3: begin
                wide = {1'b0, a} + {1'b0, b};
                y = wide[11:0];
                carry = wide[12];
            end
            4'h4: begin
                wide = {1'b0, a} - {1'b0, b};
                y = wide[11:0];
                carry = wide[12];
            end
            4'h5: y = (a * b) & 12'hfff;
            4'h6: y = (b == 12'h000) ? 12'hfff : (a / b);
            4'h7: y = a & b;
            4'h8: y = a | b;
            4'h9: y = a ^ b;
            default: y = a;
        endcase
    end

    assign zero = (y == 12'h000);
    assign neg = y[11];
endmodule
