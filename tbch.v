// Generated Z21 simulation testbench. Regenerate with zasm.py.
module tbch;
    reg clk = 1'b0;
    reg reset = 1'b1;
    wire halted;
    wire video_dirty;
    wire [7:0] pc_dbg;
    wire [2:0] flags_dbg;
    wire [11:0] r0_dbg;
    wire [11:0] r1_dbg;
    wire [11:0] r2_dbg;
    wire [11:0] r3_dbg;
    wire [11:0] r4_dbg;
    wire [11:0] r5_dbg;
    wire [11:0] r6_dbg;
    wire [11:0] r7_dbg;

    integer max_cycles;
    integer live_mode;
    integer frame_stride;
    integer frame_count;
    integer step_i;

    z21 dut(
        .clk(clk),
        .reset(reset),
        .halted(halted),
        .video_dirty(video_dirty),
        .pc_dbg(pc_dbg),
        .flags_dbg(flags_dbg),
        .r0_dbg(r0_dbg),
        .r1_dbg(r1_dbg),
        .r2_dbg(r2_dbg),
        .r3_dbg(r3_dbg),
        .r4_dbg(r4_dbg),
        .r5_dbg(r5_dbg),
        .r6_dbg(r6_dbg),
        .r7_dbg(r7_dbg)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tbch);
        max_cycles = 512;
        if (!$value$plusargs("cycles=%d", max_cycles))
            max_cycles = 512;
        live_mode = 0;
        if (!$value$plusargs("live=%d", live_mode))
            live_mode = 0;
        frame_stride = 1;
        if (!$value$plusargs("frame_stride=%d", frame_stride))
            frame_stride = 1;
        frame_count = 0;

        dut.rom[0] = 12'h100;
        dut.rom[1] = 12'h000;
        dut.rom[2] = 12'h120;
        dut.rom[3] = 12'h014;
        dut.rom[4] = 12'h140;
        dut.rom[5] = 12'h00f;
        dut.rom[6] = 12'h1a0;
        dut.rom[7] = 12'h000;
        dut.rom[8] = 12'h1c0;
        dut.rom[9] = 12'h001;
        dut.rom[10] = 12'h1e0;
        dut.rom[11] = 12'h040;
        dut.rom[12] = 12'hee8;
        dut.rom[13] = 12'he01;
        dut.rom[14] = 12'h002;
        dut.rom[15] = 12'h318;
        dut.rom[16] = 12'ha87;
        dut.rom[17] = 12'hd00;
        dut.rom[18] = 12'h00c;
        dut.rom[19] = 12'h001;

        #20 reset = 1'b0;
        for (step_i = 0; step_i < max_cycles; step_i = step_i + 1) begin
            @(negedge clk);
            dut.dump_state();
            if (live_mode && video_dirty) begin
                frame_count = frame_count + 1;
                if ((frame_count % frame_stride) == 0) begin
                    $display("FRAME_BEGIN id=%0d cycle=%0d pc=%0d live=1", frame_count, step_i, pc_dbg);
                    dut.video.dump_nonzero();
                    $display("FRAME_END id=%0d", frame_count);
                end
            end
            if (halted)
                step_i = max_cycles;
        end

        $display("FRAME_BEGIN id=%0d cycle=%0d pc=%0d live=0", frame_count + 1, step_i, pc_dbg);
        dut.video.dump_nonzero();
        $display("FRAME_END id=%0d", frame_count + 1);
        dut.dump_state();
        #1 $finish;
    end
endmodule
