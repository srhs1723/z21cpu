// Eight 12-bit registers, R0 through R7.
// Three async read ports let video instructions sample x, y, and color.
module regs(
    input clk,
    input reset,
    input we,
    input [2:0] waddr,
    input [11:0] wdata,
    input [2:0] raddr_a,
    input [2:0] raddr_b,
    input [2:0] raddr_c,
    output [11:0] rdata_a,
    output [11:0] rdata_b,
    output [11:0] rdata_c,
    output [11:0] r0,
    output [11:0] r1,
    output [11:0] r2,
    output [11:0] r3,
    output [11:0] r4,
    output [11:0] r5,
    output [11:0] r6,
    output [11:0] r7
);
    reg [11:0] bank [0:7];
    integer i;

    always @(posedge clk) begin
        if (reset) begin
            for (i = 0; i < 8; i = i + 1)
                bank[i] <= 12'h000;
        end else if (we) begin
            bank[waddr] <= wdata & 12'hfff;
        end
    end

    assign rdata_a = bank[raddr_a];
    assign rdata_b = bank[raddr_b];
    assign rdata_c = bank[raddr_c];

    assign r0 = bank[0];
    assign r1 = bank[1];
    assign r2 = bank[2];
    assign r3 = bank[3];
    assign r4 = bank[4];
    assign r5 = bank[5];
    assign r6 = bank[6];
    assign r7 = bank[7];
endmodule
