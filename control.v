// Minimal run/halt control for the Z+ core.
// The CPU owns the micro-state; this unit latches the architectural halt bit.
module control(
    input clk,
    input reset,
    input halt_req,
    output reg halt_flag,
    output running
);
    always @(posedge clk) begin
        if (reset)
            halt_flag <= 1'b0;
        else if (halt_req)
            halt_flag <= 1'b1;
    end

    assign running = !halt_flag;
endmodule
