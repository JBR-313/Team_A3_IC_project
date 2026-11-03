"""Shared figure style for the slides."""
SOURCE = "Data: Xu et al., IPIN 2026 dataset (Pixel 10 Pro + nRF54L15, UWB DW1000 ground truth)"
FIGSIZE = (10, 5.6)
DPI = 200
OUTDOOR = "#2a6fb0"
INDOOR = "#d4762a"
INK = "#2b2b2b"
MUTED = "#6b6b6b"
GRID = "#e6e6e3"


def style_axes(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)


def save(fig, out_dir, name):
    """Add the source line, then write `name` to `out_dir` and return its path."""
    fig.text(0.01, 0.01, SOURCE, color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    fig.savefig(path, dpi=DPI)
    return path
