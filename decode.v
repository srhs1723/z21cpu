// Z+ instruction decoder.
// All instruction words are 12 bits. Some opcodes consume a following
// 12-bit literal or register descriptor word.
module decode(
    input  [11:0] instr,
    output [3:0]  opcode,
    output [7:0]  sysop,
    output [2:0]  rd,
    output [2:0]  rs,
    output [1:0]  subop,
    output [2:0]  grp_a,
    output [2:0]  grp_b
);
    assign opcode = instr[11:8];
    assign sysop  = instr[7:0];
    assign rd     = instr[7:5];
    assign rs     = instr[4:2];
    assign subop  = instr[7:6];
    assign grp_a  = instr[5:3];
    assign grp_b  = instr[2:0];
endmodule
