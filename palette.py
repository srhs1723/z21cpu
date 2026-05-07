"""Cyberpunk lab palette for Z21 frame dumps."""

Z21_PALETTE = [
    "#05040a",
    "#ff2a6d",
    "#05d9e8",
    "#d1f7ff",
    "#f9f871",
    "#7cff6b",
    "#b967ff",
    "#ff8f1f",
    "#1b1f3a",
    "#4dffbf",
    "#fffb96",
    "#8be9fd",
    "#ff5555",
    "#50fa7b",
    "#bd93f9",
    "#f8f8f2",
]


def color(index):
    """Return a stable 4-bit display color."""
    return Z21_PALETTE[index & 0x0F]
