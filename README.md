# Z21 / Z+ Cyberdeck

Experimental 12-bit fantasy CPU architecture built in Verilog with a live Python/Tkinter simulation environment.

![status](https://img.shields.io/badge/status-insane-brightgreen)
![verilog](https://img.shields.io/badge/verilog-chaos-blue)
![python](https://img.shields.io/badge/python-suffering-yellow)

---

# Overview

Z21 is a custom fantasy-console / cyberdeck CPU architecture featuring:

- Custom 12-bit ISA (Z+)
- 8 general-purpose registers
- 64x48 framebuffer
- Live animation mode
- Assembly language
- Verilog CPU simulation
- Python Tkinter frontend
- GTKWave waveform debugging
- Retro graphics rendering

The project began as a tiny experimental CPU and evolved into a complete fantasy computing platform.

---

# Features

## CPU

- 12-bit architecture
- Registers: R0-R7
- Arithmetic + logic instructions
- Compare/flags
- Branching/jumps
- Label support
- 4096-value wrapping arithmetic

## Graphics

- 64x48 framebuffer
- 4-bit color palette
- VRAM rendering
- Pixel plotting
- Lines
- Rectangles
- Live framebuffer updates

## Tooling

- Assembly editor
- Live simulation mode
- Step execution
- Register viewer
- Trace logger
- Waveform generation
- Tkinter cyberdeck UI

---

# Architecture

```text
Z21 CPU
    ↓
VRAM / Framebuffer
    ↓
Python Renderer
    ↓
Tkinter Display
```

Animation is not a special CPU feature.

The CPU continuously executes normal assembly drawing code while the simulator streams framebuffer updates to the renderer.

---

# ISA Summary

## Core Instructions

```text
NOP
HALT

LDI Rn, value
MOV Rd, Rs

ADD Rd, Rs
SUB Rd, Rs
MUL Rd, Rs
DIV Rd, Rs

AND Rd, Rs
OR  Rd, Rs
XOR Rd, Rs

INC Rn
DEC Rn

CMP Ra, Rb

JMP label
JZ label
JNZ label
```

## Video Instructions

```text
CLR Rc

PSET Rx, Ry, Rc

LINE Rx0, Ry0, Rx1, Ry1, Rc

RECT Rx, Ry, Rw, Rh, Rc
```

---

# Example Program

```asm
LDI R0, 0
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
```

This animates a moving pixel across the framebuffer in Live mode.

---

# Color Palette

| ID | Color |
|----|--------|
| 0 | black |
| 1 | pink |
| 2 | cyan |
| 3 | ice white |
| 4 | yellow |
| 5 | green |
| 6 | purple |
| 7 | orange |
| 8 | navy |
| 9 | mint |
| 10 | pale yellow |
| 11 | light cyan |
| 12 | red |
| 13 | bright green |
| 14 | violet |
| 15 | white |

---

# Running

Requirements:

- Python 3
- Tkinter
- Icarus Verilog
- GTKWave

Launch:

```bash
python3 zplus_shell.py
```

---

# Live Mode

Live mode continuously:

1. Executes CPU instructions
2. Updates VRAM
3. Streams framebuffer state
4. Renders frames in Tkinter

This allows real-time animation without adding special animation instructions to the ISA.

---

# Current Status

Z21 currently supports:

- CPU simulation
- Live graphics
- Animation
- Assembly programs
- Framebuffer rendering
- Register tracing
- Waveform debugging

Planned future ideas:

- Z980 GPU
- Sprites
- Tilemaps
- Text rendering
- Sound
- Input handling
- Demo scene effects
- Tiny games

---

# Philosophy

Z21 is designed to feel like:

- a forgotten retro workstation
- a fantasy console
- an experimental cyberdeck
- an educational graphics computer

The goal is to make computer architecture visible, hackable, and fun.

---

# Screenshot

> chunky rectangles and synthwave suffering

---

# License

Apache

---

# Z21

Tiny silicon goblin architecture powered by Verilog, Python, and sleep deprivation.
