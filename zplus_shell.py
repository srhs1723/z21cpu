#!/usr/bin/env python3
"""Tkinter frontend for the Z21 Z+ retro lab."""

from __future__ import annotations

import subprocess
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import render
import zasm
from palette import color
from util import ROOT, have_tool, run_cmd

VERILOG_FILES = ["tbch.v", "z21.v", "alu.v", "regs.v", "decode.v", "vram.v", "control.v"]


class ZPlusShell(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Z21 // Z+ Cyberdeck")
        self.configure(bg="#05040a")
        self.step_cycles = 0
        self.live_proc: subprocess.Popen[str] | None = None
        self.live_queue: queue.Queue[str | None] = queue.Queue()
        self.live_parser: render.FrameStreamParser | None = None
        self.live_log: list[str] = []
        self._build_ui()
        self.editor.insert("1.0", zasm.SAMPLE)
        self.reset_view()

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Lab.TButton", padding=6, background="#1b1f3a", foreground="#d1f7ff")
        style.configure("Lab.TLabel", background="#05040a", foreground="#05d9e8")

        root = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6, bg="#1b1f3a")
        root.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(root, bg="#05040a")
        right = tk.Frame(root, bg="#05040a")
        root.add(left, minsize=360)
        root.add(right, minsize=560)

        toolbar = tk.Frame(left, bg="#05040a")
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 6))
        for text, cmd in (
            ("Run", self.run_full),
            ("Live", self.run_live),
            ("Stop", self.stop_live),
            ("Step", self.step_once),
            ("Reset", self.reset_view),
            ("Wave", self.launch_wave),
        ):
            ttk.Button(toolbar, text=text, style="Lab.TButton", command=cmd).pack(side=tk.LEFT, padx=(0, 6))

        self.editor = tk.Text(
            left,
            width=42,
            height=28,
            bg="#0b1020",
            fg="#d1f7ff",
            insertbackground="#ff2a6d",
            selectbackground="#7c2cff",
            font=("Courier", 12),
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.canvas = tk.Canvas(right, width=512, height=384, bg=color(0), highlightthickness=1, highlightbackground="#05d9e8")
        self.canvas.pack(padx=10, pady=(10, 6))

        status_frame = tk.Frame(right, bg="#05040a")
        status_frame.pack(fill=tk.X, padx=10, pady=6)
        self.status = tk.StringVar(value="idle")
        ttk.Label(status_frame, textvariable=self.status, style="Lab.TLabel").pack(anchor="w")

        self.reg_text = tk.Text(
            right,
            height=8,
            bg="#0b1020",
            fg="#f9f871",
            font=("Courier", 11),
            relief=tk.FLAT,
            padx=8,
            pady=8,
        )
        self.reg_text.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.log = tk.Text(
            right,
            height=9,
            bg="#05040a",
            fg="#8be9fd",
            font=("Courier", 9),
            relief=tk.FLAT,
            padx=8,
            pady=8,
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def reset_view(self) -> None:
        self.stop_live(update_status=False)
        self.step_cycles = 0
        render.draw_canvas(self.canvas, {}, scale=8)
        self.status.set("reset // PC 0 // Z+ waiting")
        self._show_regs({})
        self.log.delete("1.0", tk.END)

    def run_full(self) -> None:
        self.stop_live(update_status=False)
        self.step_cycles = 512
        self._assemble_compile_run(512)

    def step_once(self) -> None:
        self.stop_live(update_status=False)
        self.step_cycles += 1
        self._assemble_compile_run(self.step_cycles)

    def run_live(self) -> None:
        self.stop_live(update_status=False)
        if not self._prepare_sim():
            return
        while not self.live_queue.empty():
            try:
                self.live_queue.get_nowait()
            except queue.Empty:
                break
        self.live_parser = render.FrameStreamParser()
        self.live_log = []
        self.log.delete("1.0", tk.END)
        self.status.set("live // simulator streaming frames")
        self.live_proc = subprocess.Popen(
            ["vvp", "./z21_sim", "+cycles=2048", "+live=1", "+frame_stride=1"],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )
        threading.Thread(target=self._read_live_stdout, daemon=True).start()
        self.after(16, self._poll_live)

    def stop_live(self, update_status: bool = True) -> None:
        proc = self.live_proc
        if proc and proc.poll() is None:
            proc.terminate()
        self.live_proc = None
        if update_status:
            self.status.set("stopped // live simulator halted")

    def _read_live_stdout(self) -> None:
        proc = self.live_proc
        if not proc or not proc.stdout:
            self.live_queue.put(None)
            return
        for line in proc.stdout:
            self.live_queue.put(line)
        proc.wait()
        self.live_queue.put(None)

    def _poll_live(self) -> None:
        done = False
        painted = False
        lines_seen = 0
        while True:
            try:
                line = self.live_queue.get_nowait()
            except queue.Empty:
                break
            lines_seen += 1
            if line is None:
                done = True
                continue
            self.live_log.append(line)
            if len(self.live_log) > 500:
                self.live_log = self.live_log[-500:]
            if self.live_parser:
                view = self.live_parser.feed_line(line)
                if view is not None:
                    render.draw_canvas(self.canvas, view.pixels, scale=8)
                    self._show_regs(view.last_state)
                    self.status.set(
                        f"live // frame {len(view.frames)} // pc {view.last_state.get('pc', 0)} // pixels {len(view.pixels)}"
                    )
                    painted = True
                    break
            if lines_seen > 1000:
                break

        if self.live_log:
            self._show_log("".join(self.live_log))

        proc = self.live_proc
        if done or not proc:
            while not self.live_queue.empty():
                try:
                    self.live_queue.get_nowait()
                except queue.Empty:
                    break
            if proc and proc.returncode not in (0, None):
                self.status.set(f"live stopped // simulator exit {proc.returncode}")
            elif self.live_parser:
                self.status.set(f"live complete // frames {len(self.live_parser.view.frames)}")
            self.live_proc = None
            return
        self.after(16 if painted else 5, self._poll_live)

    def _prepare_sim(self) -> bool:
        source = self.editor.get("1.0", tk.END)
        try:
            words = zasm.assemble_text(source)
            zasm.write_tbch(words)
        except zasm.AsmError as exc:
            messagebox.showerror("Z+ assembler", str(exc))
            return False

        if not have_tool("iverilog") or not have_tool("vvp"):
            messagebox.showerror("Icarus Verilog missing", "Install iverilog and vvp, then rerun build.sh.")
            return False

        code, out = run_cmd(["iverilog", "-g2012", "-o", "z21_sim", *VERILOG_FILES], ROOT)
        if code != 0:
            self._show_log(out)
            messagebox.showerror("Icarus compile failed", out[:1000])
            return False
        return True

    def _assemble_compile_run(self, cycles: int) -> None:
        if not self._prepare_sim():
            return

        code, sim_out = run_cmd(["vvp", "./z21_sim", f"+cycles={cycles}"], ROOT)
        view = render.parse_sim_output(sim_out)
        render.draw_canvas(self.canvas, view.pixels, scale=8)
        self._show_regs(view.last_state)
        self._show_log(sim_out)
        halted = view.last_state.get("halted", 0)
        self.status.set(f"cycles {cycles} // pc {view.last_state.get('pc', 0)} // halted {halted} // pixels {len(view.pixels)}")
        if code != 0:
            messagebox.showerror("Simulation failed", sim_out[:1000])

    def _show_regs(self, state: dict[str, int]) -> None:
        state = {"pc": 0, "halted": 0, "z": 0, "c": 0, "n": 0, **{f"r{i}": 0 for i in range(8)}, **state}
        lines = [
            f"PC {state['pc']:03d}   HALT {state['halted']}   Z {state['z']} C {state['c']} N {state['n']}",
            " ".join(f"R{i}:{state[f'r{i}']:03x}" for i in range(4)),
            " ".join(f"R{i}:{state[f'r{i}']:03x}" for i in range(4, 8)),
        ]
        self.reg_text.delete("1.0", tk.END)
        self.reg_text.insert("1.0", "\n".join(lines))

    def _show_log(self, text: str) -> None:
        self.log.delete("1.0", tk.END)
        self.log.insert("1.0", text[-6000:])
        self.log.see(tk.END)

    def launch_wave(self) -> None:
        wave = ROOT / "wave.vcd"
        if not wave.exists():
            messagebox.showinfo("Waveform", "Run or step first to generate wave.vcd.")
            return
        if not have_tool("gtkwave"):
            messagebox.showinfo("Waveform", "wave.vcd exists. Install gtkwave to open it from this button.")
            return
        subprocess.Popen(["gtkwave", str(wave)])


def main() -> int:
    app = ZPlusShell()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
