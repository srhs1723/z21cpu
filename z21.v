// Z21: an experimental Z+ 12-bit fantasy CPU.
// Retro console devkit rules:
// - 8 general registers, R0-R7
// - 8-bit program counter over 256 words of embedded ROM
// - zero/carry/negative flags
// - small scratch RAM for future experiments
// - 64x48 4-bit VRAM framebuffer
module z21(
    input clk,
    input reset,
    output halted,
    output video_dirty,
    output [7:0] pc_dbg,
    output [2:0] flags_dbg,
    output [11:0] r0_dbg,
    output [11:0] r1_dbg,
    output [11:0] r2_dbg,
    output [11:0] r3_dbg,
    output [11:0] r4_dbg,
    output [11:0] r5_dbg,
    output [11:0] r6_dbg,
    output [11:0] r7_dbg
);
    localparam S_FETCH = 3'd0;
    localparam S_EXEC  = 3'd1;
    localparam S_VIDEO = 3'd2;

    reg [11:0] rom [0:255];
    reg [11:0] ram [0:31];
    reg [7:0] pc;
    reg [11:0] instr;
    reg [2:0] state;
    reg [2:0] video_kind;
    reg [5:0] video_x0;
    reg [5:0] video_y0;
    reg [2:0] flags;
    reg [31:0] cycles;
    reg video_dirty_reg;

    reg reg_we;
    reg [2:0] reg_waddr;
    reg [11:0] reg_wdata;
    reg [2:0] read_a;
    reg [2:0] read_b;
    reg [2:0] read_c;

    wire running;
    wire [3:0] opcode;
    wire [7:0] sysop;
    wire [2:0] rd;
    wire [2:0] rs;
    wire [1:0] subop;
    wire [2:0] grp_a;
    wire [2:0] grp_b;

    wire [11:0] ra;
    wire [11:0] rb;
    wire [11:0] rc;
    wire [11:0] alu_y;
    wire alu_carry;
    wire alu_zero;
    wire alu_neg;
    wire halt_decode;

    integer i;

    initial begin
        for (i = 0; i < 256; i = i + 1)
            rom[i] = 12'h000;
        for (i = 0; i < 32; i = i + 1)
            ram[i] = 12'h000;
        pc = 8'h00;
        instr = 12'h000;
        state = S_FETCH;
        video_kind = 3'd0;
        video_x0 = 6'd0;
        video_y0 = 6'd0;
        flags = 3'b000;
        cycles = 0;
        video_dirty_reg = 1'b0;
    end

    decode decoder(
        .instr(instr),
        .opcode(opcode),
        .sysop(sysop),
        .rd(rd),
        .rs(rs),
        .subop(subop),
        .grp_a(grp_a),
        .grp_b(grp_b)
    );

    regs regfile(
        .clk(clk),
        .reset(reset),
        .we(reg_we),
        .waddr(reg_waddr),
        .wdata(reg_wdata),
        .raddr_a(read_a),
        .raddr_b(read_b),
        .raddr_c(read_c),
        .rdata_a(ra),
        .rdata_b(rb),
        .rdata_c(rc),
        .r0(r0_dbg),
        .r1(r1_dbg),
        .r2(r2_dbg),
        .r3(r3_dbg),
        .r4(r4_dbg),
        .r5(r5_dbg),
        .r6(r6_dbg),
        .r7(r7_dbg)
    );

    alu core_alu(
        .op(opcode),
        .a(ra),
        .b(rb),
        .y(alu_y),
        .carry(alu_carry),
        .zero(alu_zero),
        .neg(alu_neg)
    );

    control ctl(
        .clk(clk),
        .reset(reset),
        .halt_req(halt_decode),
        .halt_flag(halted),
        .running(running)
    );

    vram video(
        .clk(clk),
        .we(1'b0),
        .write_x(6'd0),
        .write_y(6'd0),
        .write_color(4'd0),
        .read_x(6'd0),
        .read_y(6'd0),
        .read_color()
    );

    always @* begin
        read_a = rd;
        read_b = rs;
        read_c = 3'd0;
        reg_we = 1'b0;
        reg_waddr = rd;
        reg_wdata = 12'h000;

        if (state == S_EXEC) begin
            case (opcode)
                4'h1: begin
                    reg_we = 1'b1;
                    reg_waddr = rd;
                    reg_wdata = rom[pc];
                end
                4'h2: begin
                    reg_we = 1'b1;
                    reg_waddr = rd;
                    reg_wdata = rb;
                end
                4'h3, 4'h4, 4'h5, 4'h6, 4'h7, 4'h8, 4'h9: begin
                    reg_we = 1'b1;
                    reg_waddr = rd;
                    reg_wdata = alu_y;
                end
                4'ha: begin
                    read_a = grp_a;
                    read_b = grp_b;
                    reg_waddr = grp_a;
                    if (subop == 2'b00) begin
                        reg_we = 1'b1;
                        reg_wdata = ra + 12'h001;
                    end else if (subop == 2'b01) begin
                        reg_we = 1'b1;
                        reg_wdata = ra - 12'h001;
                    end
                end
                4'he: begin
                    read_a = grp_a;
                    read_b = grp_b;
                    if (subop == 2'b11)
                        read_c = grp_a;
                end
                default: begin
                end
            endcase
        end else if (state == S_VIDEO) begin
            read_a = instr[5:3];
            read_b = instr[2:0];
            read_c = rom[pc][5:3];
            if (video_kind == 3'd0)
                read_c = rom[pc][2:0];
            else begin
                read_a = rom[pc][11:9];
                read_b = rom[pc][8:6];
                read_c = rom[pc][5:3];
            end
        end
    end

    always @(posedge clk) begin
        if (reset) begin
            pc <= 8'h00;
            instr <= 12'h000;
            state <= S_FETCH;
            video_kind <= 3'd0;
            video_x0 <= 6'd0;
            video_y0 <= 6'd0;
            flags <= 3'b000;
            cycles <= 0;
            video_dirty_reg <= 1'b0;
        end else if (running) begin
            cycles <= cycles + 1;
            video_dirty_reg <= 1'b0;

            case (state)
                S_FETCH: begin
                    instr <= rom[pc];
                    pc <= pc + 8'd1;
                    state <= S_EXEC;
                end
                S_EXEC: begin
                    case (opcode)
                        4'h0: begin
                            if (sysop == 8'h01) begin
                            end
                        end
                        4'h1: begin
                            pc <= pc + 8'd1;
                            flags[0] <= (rom[pc] == 12'h000);
                            flags[1] <= 1'b0;
                            flags[2] <= rom[pc][11];
                        end
                        4'h2: begin
                            flags[0] <= (rb == 12'h000);
                            flags[1] <= 1'b0;
                            flags[2] <= rb[11];
                        end
                        4'h3, 4'h4, 4'h5, 4'h6, 4'h7, 4'h8, 4'h9: begin
                            flags[0] <= alu_zero;
                            flags[1] <= alu_carry;
                            flags[2] <= alu_neg;
                        end
                        4'ha: begin
                            if (subop == 2'b00) begin
                                flags[0] <= ((ra + 12'h001) == 12'h000);
                                flags[1] <= (ra == 12'hfff);
                                flags[2] <= ((ra + 12'h001) & 12'h800) != 12'h000;
                            end else if (subop == 2'b01) begin
                                flags[0] <= ((ra - 12'h001) == 12'h000);
                                flags[1] <= (ra == 12'h000);
                                flags[2] <= ((ra - 12'h001) & 12'h800) != 12'h000;
                            end else if (subop == 2'b10) begin
                                flags[0] <= (ra == rb);
                                flags[1] <= (ra < rb);
                                flags[2] <= ((ra - rb) & 12'h800) != 12'h000;
                            end
                        end
                        4'hb: pc <= rom[pc][7:0];
                        4'hc: begin
                            if (flags[0])
                                pc <= rom[pc][7:0];
                            else
                                pc <= pc + 8'd1;
                        end
                        4'hd: begin
                            if (!flags[0])
                                pc <= rom[pc][7:0];
                            else
                                pc <= pc + 8'd1;
                        end
                        4'he: begin
                            if (subop == 2'b11) begin
                                video.clear_all(ra[3:0]);
                                video_dirty_reg <= 1'b1;
                            end else begin
                                video_x0 <= ra[5:0];
                                video_y0 <= rb[5:0];
                                video_kind <= {1'b0, subop};
                                state <= S_VIDEO;
                            end
                        end
                        default: begin
                        end
                    endcase

                    if (opcode != 4'he || subop == 2'b11)
                        state <= S_FETCH;
                end
                S_VIDEO: begin
                    if (video_kind == 3'd0)
                        video.pset(video_x0, video_y0, rc[3:0]);
                    else if (video_kind == 3'd1)
                        video.draw_line(video_x0, video_y0, ra[5:0], rb[5:0], rc[3:0]);
                    else if (video_kind == 3'd2)
                        video.draw_rect(video_x0, video_y0, ra[5:0], rb[5:0], rc[3:0]);

                    video_dirty_reg <= 1'b1;
                    pc <= pc + 8'd1;
                    state <= S_FETCH;
                end
                default: state <= S_FETCH;
            endcase
        end
    end

    assign pc_dbg = pc;
    assign flags_dbg = flags;
    assign video_dirty = video_dirty_reg;
    assign halt_decode = (state == S_EXEC && opcode == 4'h0 && sysop == 8'h01);

    task dump_state;
        begin
            $display("STATE cycle=%0d pc=%0d halted=%0d z=%0d c=%0d n=%0d r0=%0d r1=%0d r2=%0d r3=%0d r4=%0d r5=%0d r6=%0d r7=%0d",
                cycles, pc, halted, flags[0], flags[1], flags[2],
                r0_dbg, r1_dbg, r2_dbg, r3_dbg, r4_dbg, r5_dbg, r6_dbg, r7_dbg);
        end
    endtask
endmodule
