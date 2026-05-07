"""Shared helpers for the Z21 devkit tools."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def have_tool(name: str) -> bool:
    return shutil.which(name) is not None


def run_cmd(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode, proc.stdout


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))
