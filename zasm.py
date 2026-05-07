#!/usr/bin/env python3
"""Assembler for Z+ assembly and generator for tbch.v."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from util import ROOT, write_text

SAMPLE = """LDI R0, 0
LDI R1, 20
LDI R2, 15
LDI R5, 0
LDI R6, 1
LDI R7, 64
loop:
CLR R5
PSET R0, R1, R2
ADD R0, R6
CMP R0, R7
JNZ loop
HALT
"""

REG_RE = re.compile(r"^R([0-7])$", re.IGNORECASE)
TOKEN_RE = re.compile(r"[,\s]+")
SYS = {"NOP": 0x000, "HALT": 0x001}
REG_OPS = {
    "MOV": 0x2,
    "ADD": 0x3,
    "SUB": 0x4,
    "MUL": 0x5,
    "DIV": 0x6,
    "AND": 0x7,
    "OR": 0x8,
    "XOR": 0x9,
}
GROUP_OPS = {"INC": 0, "DEC": 1, "CMP": 2}
JUMPS = {"JMP": 0xB, "JZ": 0xC, "JNZ": 0xD}


class AsmError(Exception):
    pass


def strip_comment(line: str) -> str:
    for marker in (";", "#"):
        if marker in line:
            line = line.split(marker, 1)[0]
    return line.strip()


def parse_reg(token: str) -> int:
    match = REG_RE.match(token.strip())
    if not match:
        raise AsmError(f"expected register R0-R7, got {token!r}")
    return int(match.group(1))


def parse_num(token: str, labels: dict[str, int]) -> int:
    token = token.strip()
    if token in labels:
        return labels[token]
    try:
        return int(token, 0) & 0xFFF
    except ValueError as exc:
        raise AsmError(f"unknown number or label {token!r}") from exc


def tokenize(line: str) -> list[str]:
    return [part for part in TOKEN_RE.split(line.strip()) if part]


def normalized_lines(source: str) -> list[tuple[int, str]]:
    out = []
    for lineno, raw in enumerate(source.splitlines(), 1):
        line = strip_comment(raw)
        if line:
            out.append((lineno, line))
    return out


def instr_size(tokens: list[str]) -> int:
    op = tokens[0].upper()
    if op in {"LDI", "JMP", "JZ", "JNZ", "PSET", "LINE", "RECT"}:
        return 2
    if op in REG_OPS and op != "MOV" and len(tokens) == 4:
        return 2
    return 1


def first_pass(lines: list[tuple[int, str]]) -> tuple[dict[str, int], list[tuple[int, str]]]:
    labels: dict[str, int] = {}
    code: list[tuple[int, str]] = []
    pc = 0
    for lineno, line in lines:
        while ":" in line:
            label, rest = line.split(":", 1)
            label = label.strip()
            if not label:
                raise AsmError(f"line {lineno}: empty label")
            labels[label] = pc
            line = rest.strip()
            if not line:
                break
        if line:
            tokens = tokenize(line)
            pc += instr_size(tokens)
            code.append((lineno, line))
        if pc > 256:
            raise AsmError("program exceeds 256 words")
    return labels, code


def encode_line(line: str, labels: dict[str, int]) -> list[int]:
    tokens = tokenize(line)
    if not tokens:
        return []
    op = tokens[0].upper()

    if op in SYS:
        if len(tokens) != 1:
            raise AsmError(f"{op} takes no operands")
        return [SYS[op]]

    if op == "LDI":
        if len(tokens) != 3:
            raise AsmError("LDI syntax: LDI Rn, value")
        return [0x100 | (parse_reg(tokens[1]) << 5), parse_num(tokens[2], labels)]

    if op in REG_OPS:
        if op != "MOV" and len(tokens) == 4:
            rd = parse_reg(tokens[1])
            ra = parse_reg(tokens[2])
            rb = parse_reg(tokens[3])
            return [
                (REG_OPS["MOV"] << 8) | (rd << 5) | (ra << 2),
                (REG_OPS[op] << 8) | (rd << 5) | (rb << 2),
            ]
        if len(tokens) != 3:
            raise AsmError(f"{op} syntax: {op} Rd, Rs")
        rd = parse_reg(tokens[1])
        rs = parse_reg(tokens[2])
        return [(REG_OPS[op] << 8) | (rd << 5) | (rs << 2)]

    if op in GROUP_OPS:
        sub = GROUP_OPS[op]
        if op in {"INC", "DEC"}:
            if len(tokens) != 2:
                raise AsmError(f"{op} syntax: {op} Rn")
            return [0xA00 | (sub << 6) | (parse_reg(tokens[1]) << 3)]
        if len(tokens) != 3:
            raise AsmError("CMP syntax: CMP Ra, Rb")
        return [0xA00 | (sub << 6) | (parse_reg(tokens[1]) << 3) | parse_reg(tokens[2])]

    if op in JUMPS:
        if len(tokens) != 2:
            raise AsmError(f"{op} syntax: {op} label")
        return [(JUMPS[op] << 8), parse_num(tokens[1], labels)]

    if op == "PSET":
        if len(tokens) != 4:
            raise AsmError("PSET syntax: PSET Rx, Ry, Rc")
        return [0xE00 | (parse_reg(tokens[1]) << 3) | parse_reg(tokens[2]), parse_reg(tokens[3])]

    if op == "LINE":
        if len(tokens) != 6:
            raise AsmError("LINE syntax: LINE Rx0, Ry0, Rx1, Ry1, Rc")
        return [
            0xE00 | (1 << 6) | (parse_reg(tokens[1]) << 3) | parse_reg(tokens[2]),
            (parse_reg(tokens[3]) << 9) | (parse_reg(tokens[4]) << 6) | (parse_reg(tokens[5]) << 3),
        ]

    if op == "RECT":
        if len(tokens) != 6:
            raise AsmError("RECT syntax: RECT Rx, Ry, Rw, Rh, Rc")
        return [
            0xE00 | (2 << 6) | (parse_reg(tokens[1]) << 3) | parse_reg(tokens[2]),
            (parse_reg(tokens[3]) << 9) | (parse_reg(tokens[4]) << 6) | (parse_reg(tokens[5]) << 3),
        ]

    if op == "CLR":
        if len(tokens) != 2:
            raise AsmError("CLR syntax: CLR Rc")
        return [0xE00 | (3 << 6) | (parse_reg(tokens[1]) << 3)]

    raise AsmError(f"unknown opcode {op!r}")


def assemble_text(source: str) -> list[int]:
    labels, code = first_pass(normalized_lines(source))
    words: list[int] = []
    for lineno, line in code:
        try:
            words.extend(encode_line(line, labels))
        except AsmError as exc:
            raise AsmError(f"line {lineno}: {exc}") from exc
    if len(words) > 256:
        raise AsmError("program exceeds 256 words")
    return [word & 0xFFF for word in words]


def tbch_text(words: list[int]) -> str:
    assigns = "\n".join(f"        dut.rom[{i}] = 12'h{word:03x};" for i, word in enumerate(words))
    if not assigns:
        assigns = "        dut.rom[0] = 12'h001;"
    return f"""// Generated Z21 simulation testbench. Regenerate with zasm.py.
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

{assigns}

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
"""


def write_tbch(words: list[int], path: Path | None = None) -> None:
    write_text(path or ROOT / "tbch.v", tbch_text(words))


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble Z+ source into embedded Verilog testbench")
    parser.add_argument("source", nargs="?", help="assembly source file")
    parser.add_argument("--sample", action="store_true", help="generate tbch.v from the built-in sample")
    parser.add_argument("--out", default=str(ROOT / "tbch.v"), help="testbench output path")
    args = parser.parse_args()

    if args.sample or not args.source:
        source = SAMPLE
    else:
        source = Path(args.source).read_text(encoding="utf-8")

    write_tbch(assemble_text(source), Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
