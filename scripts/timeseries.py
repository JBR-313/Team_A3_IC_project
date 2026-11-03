"""Plot CS against UWB over time: the indoor 10 m outlier check, Figure B, and Figure C."""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from align import TOLERANCE, align, load_gt
from style import FIGSIZE, INDOOR, INK, OUTDOOR, save, style_axes

INDOOR_10M = "Static_5Hz_10m_Indoor_Corridor"
OUTDOOR_10M = "Static_5Hz_10m_Outdoor"
WALK = "Dynamic_10Hz_Outdoor"
DUPLICATE_WINDOW = 0.005  # seconds
LAGS = [lag / 10 for lag in range(-50, 51)]  # seconds
ERROR_BANDS = ((0, 2), (2, 10), (10, float("inf")))  # metres
# Not the outdoor/indoor colors used by the other figures: here color means confidence.
CONFIDENCE_STYLES = {
    2: {"label": "High confidence (2)", "color": "#5b4bc4", "marker": "o"},
    1: {"label": "Medium confidence (1)", "color": "#2f8f6b", "marker": "s"},
    0: {"label": "Low confidence (0)", "color": "#c98500", "marker": "x"},
}


def prepare(data_dir, scenario):
    """Aligned rows plus `s` = seconds from the first sample and `repeat` = near-duplicate flag."""
    m = align(data_dir, scenario).dropna(subset=["err"]).reset_index(drop=True)
    m["s"] = (m["t"] - m["t"].min()).dt.total_seconds()
    m["repeat"] = (m["s"].diff() <= DUPLICATE_WINDOW) & (m["Distance (m)"].diff() == 0)
    return m


def summarize_outlier(m):
    """Print the numbers used to interpret the indoor 10 m plot."""
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


def lagged_median_error(m, gt, lag):
    """Median absolute error if each CS sample is compared with UWB `lag` seconds earlier."""
    shifted_t = (m["t"] - pd.Timedelta(seconds=lag)).astype(gt["t"].dtype)
    shifted = m[["Distance (m)"]].assign(t=shifted_t)
    paired = pd.merge_asof(shifted, gt[["t", "Distance(m)"]], on="t", direction="nearest", tolerance=TOLERANCE)
    return (paired["Distance (m)"] - paired["Distance(m)"]).abs().median()


def walk_stats(data_dir):
    """One row per dynamic scenario, so Figure C can be read against the other walks."""
    rows = []
    for path in sorted((Path(data_dir) / "RangingFilter").glob("Dynamic_*.csv")):
        m = prepare(data_dir, path.stem)
        gt = load_gt(data_dir, path.stem)
        by_lag = {lag: lagged_median_error(m, gt, lag) for lag in LAGS}
        best = min(by_lag, key=by_lag.get)
        rows.append({
            "scenario": path.stem,
            "n": len(m),
            "median_abs": m["err"].abs().median(),
            "MAE": m["err"].abs().mean(),
            "P95": m["err"].abs().quantile(0.95),
            "best_lag_s": best,
            "median_abs_at_lag": by_lag[best],
        })
    return pd.DataFrame(rows)


def draw_reference(ax, m):
    ax.plot(m["s"], m["Distance(m)"], color=INK, linewidth=2, zorder=4, label="UWB reference")
    style_axes(ax)
    ax.set_xlim(0, None)
    ax.set_ylim(0, None)
    ax.set_ylabel("Distance (m)", color=INK)


def draw_cs(ax, m, color, marker):
    ax.scatter(m["s"], m["Distance (m)"], s=26, color=color, marker=marker, linewidths=0,
               alpha=0.75, zorder=3, label="CS")


def plot_outlier(m, out_dir):
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for level, style in CONFIDENCE_STYLES.items():
        group = m[m["Confidence Level"] == level]
        if group.empty:
            continue
        ax.scatter(group["s"], group["Distance (m)"], s=26, linewidths=1.2 if style["marker"] == "x" else 0,
                   alpha=0.75, zorder=3, **style)
    draw_reference(ax, m)
    ax.set_xlabel("Time since first sample (s)", color=INK)
    ax.legend(loc="lower right", frameon=False, ncols=3, labelcolor=INK)
    ax.set_title(f"CS vs. UWB over time: {INDOOR_10M}", loc="left", color=INK, fontsize=13)
    path = save(fig, out_dir, f"timeseries_{INDOOR_10M}.png")
    plt.close(fig)
    return path


def plot_figure_b(outdoor, indoor, out_dir):
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE, sharex=True, sharey=True)
    panels = ((outdoor, "Outdoor", OUTDOOR, "o"), (indoor, "Indoor corridor", INDOOR, "s"))
    for ax, (m, name, color, marker) in zip(axes, panels):
        draw_cs(ax, m, color, marker)
        draw_reference(ax, m)
        ax.set_title(f"{name}: MAE {m['err'].abs().mean():.2f} m", loc="left", color=INK, fontsize=11)
        ax.set_ylim(0, 48)
        ax.legend(loc="center right", frameon=False, ncols=2, labelcolor=INK)
    axes[1].set_xlabel("Time since first sample (s)", color=INK)
    fig.suptitle("The same 10 m at 5 Hz, in two environments", x=0.01, ha="left", color=INK, fontsize=13)
    path = save(fig, out_dir, "figure_b_10m_comparison.png")
    plt.close(fig)
    return path


def plot_figure_c(m, out_dir):
    fig, ax = plt.subplots(figsize=FIGSIZE)
    draw_cs(ax, m, OUTDOOR, "o")
    draw_reference(ax, m)
    ax.set_xlabel("Time since first sample (s)", color=INK)
    ax.legend(loc="upper left", frameon=False, ncols=2, labelcolor=INK)
    ax.set_title(f"CS tracking UWB during a walk: {WALK}", loc="left", color=INK, fontsize=13)
    path = save(fig, out_dir, "figure_c_walk.png")
    plt.close(fig)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=Path("figures"))
    args = parser.parse_args()

    indoor = prepare(args.data, INDOOR_10M)
    outdoor = prepare(args.data, OUTDOOR_10M)
    walk = prepare(args.data, WALK)
    summarize_outlier(indoor)
    print("\nwalks")
    print(walk_stats(args.data).round(2).to_string(index=False))
    print(f"\nsaved {plot_outlier(indoor, args.out)}")
    print(f"saved {plot_figure_b(outdoor, indoor, args.out)}")
    print(f"saved {plot_figure_c(walk, args.out)}")


if __name__ == "__main__":
    main()
