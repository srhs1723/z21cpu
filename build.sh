#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

rm -f z21_sim wave.vcd sim.out
find . -maxdepth 1 -type d -name "__pycache__" -exec rm -rf {} +

python3 zasm.py --sample
iverilog -g2012 -o z21_sim tbch.v z21.v alu.v regs.v decode.v vram.v control.v
python3 zplus_shell.py
