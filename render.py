"""Parse Icarus Verilog Z21 output and render the 64x48 framebuffer."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field

from palette import color

WIDTH = 64
HEIGHT = 48
STATE_RE = re.compile(
    r"STATE cycle=(?P<cycle>\d+) pc=(?P<pc>\d+) halted=(?P<halted>\d+) "
    r"z=(?P<z>\d+) c=(?P<c>\d+) n=(?P<n>\d+) "
    r"r0=(?P<r0>\d+) r1=(?P<r1>\d+) r2=(?P<r2>\d+) r3=(?P<r3>\d+) "
    r"r4=(?P<r4>\d+) r5=(?P<r5>\d+) r6=(?P<r6>\d+) r7=(?P<r7>\d+)"
)


@dataclass
class SimView:
    pixels: dict[tuple[int, int], int] = field(default_factory=dict)
    frames: list[dict[tuple[int, int], int]] = field(default_factory=list)
    states: list[dict[str, int]] = field(default_factory=list)
    log: str = ""

    @property
    def last_state(self) -> dict[str, int]:
        if self.states:
            return self.states[-1]
        return {"cycle": 0, "pc": 0, "halted": 0, "z": 0, "c": 0, "n": 0, **{f"r{i}": 0 for i in range(8)}}


def parse_sim_output(text: str) -> SimView:
    view = SimView(log=text)
    in_frame = False
    frame_pixels: dict[tuple[int, int], int] = {}
    for line in text.splitlines():
        if line.startswith("FRAME_BEGIN"):
            in_frame = True
            frame_pixels = {}
            continue
        if line.startswith("FRAME_END"):
            in_frame = False
            view.pixels = frame_pixels
            view.frames.append(dict(frame_pixels))
            continue
        if in_frame and line.startswith("FB "):
            _, xs, ys, cs = line.split()
            x, y, c = int(xs), int(ys), int(cs)
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                frame_pixels[(x, y)] = c & 0xF
            continue
        match = STATE_RE.match(line)
        if match:
            view.states.append({k: int(v) for k, v in match.groupdict().items()})
    return view


class FrameStreamParser:
    """Incrementally parse simulator stdout into complete framebuffer frames."""

    def __init__(self) -> None:
        self.view = SimView()
        self._frame_pixels: dict[tuple[int, int], int] | None = None

    def feed_line(self, line: str) -> SimView | None:
        line = line.rstrip("\n")
        if line.startswith("FRAME_BEGIN"):
            self._frame_pixels = {}
            return None
        if line.startswith("FRAME_END"):
            if self._frame_pixels is not None:
                self.view.pixels = self._frame_pixels
                self.view.frames.append(dict(self._frame_pixels))
                self._frame_pixels = None
                return self.view
            return None
        if self._frame_pixels is not None and line.startswith("FB "):
            _, xs, ys, cs = line.split()
            x, y, c = int(xs), int(ys), int(cs)
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                self._frame_pixels[(x, y)] = c & 0xF
            return None
        match = STATE_RE.match(line)
        if match:
            self.view.states.append({k: int(v) for k, v in match.groupdict().items()})
        return None


def draw_canvas(canvas, pixels: dict[tuple[int, int], int], scale: int = 8) -> None:
    canvas.delete("all")
    canvas.configure(width=WIDTH * scale, height=HEIGHT * scale, bg=color(0))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            c = pixels.get((x, y), 0)
            if c:
                canvas.create_rectangle(
                    x * scale,
                    y * scale,
                    (x + 1) * scale,
                    (y + 1) * scale,
                    fill=color(c),
                    outline=color(c),
                )


def text_frame(pixels: dict[tuple[int, int], int]) -> str:
    rows = []
    for y in range(HEIGHT):
        row = []
        for x in range(WIDTH):
            c = pixels.get((x, y), 0)
            row.append(" ." if c == 0 else f"{c:02x}")
        rows.append(" ".join(row))
    return "\n".join(rows)


def main() -> int:
    data = sys.stdin.read()
    view = parse_sim_output(data)
    print(text_frame(view.pixels))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
