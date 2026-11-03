"""Plot CS against UWB over time, colored by confidence level (README: indoor 10 m outlier check)."""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from align import align

SCENARIO = "Static_5Hz_10m_Indoor_Corridor"
SOURCE = "Data: Xu et al., IPIN 2026 dataset (Pixel 10 Pro + nRF54L15, UWB DW1000 ground truth)"
DUPLICATE_WINDOW = 0.005  # seconds
ERROR_BANDS = ((0, 2), (2, 10), (10, float("inf")))  # metres
INK = "#2b2b2b"
MUTED = "#6b6b6b"
GRID = "#e6e6e3"
# Not the outdoor/indoor colors used by the other figures: here color means confidence.
CONFIDENCE_STYLES = {
    2: {"label": "High confidence (2)", "color": "#5b4bc4", "marker": "o"},
    1: {"label": "Medium confidence (1)", "color": "#2f8f6b", "marker": "s"},
    0: {"label": "Low confidence (0)", "color": "#c98500", "marker": "x"},
}


def prepare(data_dir, scenario):
    """Aligned rows plus `s` = seconds from the first sample and `repeat` = near-duplicate flag."""
    m = align(data_dir, scenario).reset_index(drop=True)
    m["s"] = (m["t"] - m["t"].min()).dt.total_seconds()
    m["repeat"] = (m["s"].diff() <= DUPLICATE_WINDOW) & (m["Distance (m)"].diff() == 0)
    return m


def summarize(m):
    """Print the numbers used to interpret the plot."""
    print(f"samples: {len(m)}, repeats within {DUPLICATE_WINDOW * 1000:.0f} ms: {m['repeat'].sum()}")
    unique = m[~m["repeat"]]
    print(f"MAE: all {m['err'].abs().mean():.2f} m, without repeats {unique['err'].abs().mean():.2f} m")
    print(f"all errors positive: {(m['err'] > 0).all()}, min {m['err'].min():.2f} m")

    print("\nmedian error by time")
    for start, group in m.groupby(m["s"] // 10 * 10):
        print(f"  {start:3.0f}-{start + 10:3.0f} s: {group['err'].median():6.2f} m (n={len(group)})")

    print("\nerror by confidence level")
    for level, group in m.groupby("Confidence Level"):
        print(f"  {level}: n={len(group)}, MAE={group['err'].abs().mean():.2f} m, "
              f"median={group['err'].median():.2f} m, max={group['err'].max():.2f} m")

    print("\nlow-confidence share by error")
    for lo, hi in ERROR_BANDS:
        band = m[(m["err"] >= lo) & (m["err"] < hi)]
        print(f"  {lo}-{hi} m: {(band['Confidence Level'] == 0).mean():.0%} of {len(band)} "
              f"({len(band) / len(m):.0%} of samples)")


def plot(m, scenario, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5.6))
    for level, style in CONFIDENCE_STYLES.items():
        group = m[m["Confidence Level"] == level]
        if group.empty:
            continue
        ax.scatter(group["s"], group["Distance (m)"], s=26, linewidths=1.2 if style["marker"] == "x" else 0,
                   alpha=0.75, zorder=3, **style)

    ax.plot(m["s"], m["Distance(m)"], color=INK, linewidth=2, zorder=4, label="UWB reference")

    ax.set_xlabel("Time since first sample (s)", color=INK)
    ax.set_ylabel("Distance (m)", color=INK)
    ax.set_xlim(0, m["s"].max() + 1)
    ax.set_ylim(0, None)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.legend(loc="lower right", frameon=False, ncols=3, labelcolor=INK)

    ax.set_title(f"CS vs. UWB over time: {scenario}", loc="left", color=INK, fontsize=13)
    fig.text(0.01, 0.01, SOURCE, color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"timeseries_{scenario}.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=Path("figures"))
    parser.add_argument("--scenario", default=SCENARIO)
    args = parser.parse_args()

    m = prepare(args.data, args.scenario)
    summarize(m)
    print(f"\nsaved {plot(m, args.scenario, args.out)}")


if __name__ == "__main__":
    main()
