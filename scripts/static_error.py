"""Compute static error statistics and plot Figure A: error by distance, outdoor vs. indoor."""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from align import align
from style import FIGSIZE, INDOOR, INK, OUTDOOR, save, style_axes

ENVIRONMENTS = {
    "Outdoor": {"color": OUTDOOR, "marker": "o", "label_offset": (-6, 8), "label_ha": "right"},
    "Indoor": {"color": INDOOR, "marker": "s", "label_offset": (8, 6), "label_ha": "left"},
}
PANELS = {"MAE": "Mean absolute error", "P95": "95th percentile of absolute error"}


def scenario_stats(data_dir):
    """One row per static scenario, as in the README table."""
    rows = []
    for path in sorted((Path(data_dir) / "RangingFilter").glob("Static_*.csv")):
        err = align(data_dir, path.stem)["err"].dropna()
        _, _, distance, environment = path.stem.split("_", 3)
        rows.append({
            "scenario": path.stem,
            "environment": environment.split("_")[0],
            "distance": int(distance.removesuffix("m")),
            "n": len(err),
            "mean": err.mean(),
            "MAE": err.abs().mean(),
            "std": err.std(),
            "P95": err.abs().quantile(0.95),
            "RMSE": np.sqrt((err ** 2).mean()),
        })
    return pd.DataFrame(rows)


def combine_rates(stats):
    """Merge update rates per environment and distance with an n-weighted average."""
    def weighted(group):
        return pd.Series({
            "n": group["n"].sum(),
            "MAE": np.average(group["MAE"], weights=group["n"]),
            "P95": np.average(group["P95"], weights=group["n"]),
        })

    return stats.groupby(["environment", "distance"])[["n", "MAE", "P95"]].apply(weighted).reset_index()


def plot(combined, out_dir):
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE, sharex=True, sharey=True)
    for ax, (metric, title) in zip(axes, PANELS.items()):
        for environment, style in ENVIRONMENTS.items():
            group = combined[combined["environment"] == environment]
            ax.plot(group["distance"], group[metric], linewidth=2, markersize=8, markeredgecolor="white",
                    label=environment, color=style["color"], marker=style["marker"])
            at_10m = group[group["distance"] == 10].iloc[0]
            ax.annotate(f"{environment} 10 m: {at_10m[metric]:.2f} m", (10, at_10m[metric]),
                        xytext=style["label_offset"], textcoords="offset points", ha=style["label_ha"],
                        color=INK, fontsize=9)
        style_axes(ax)
        ax.set_xscale("log")
        ax.set_xticks([1, 10, 25, 50], labels=["1", "10", "25", "50"])
        ax.minorticks_off()
        ax.set_ylim(0, 13)
        ax.set_title(title, loc="left", color=INK, fontsize=11)
        ax.set_xlabel("Distance (m, log scale)", color=INK)
    axes[0].set_ylabel("Error (m)", color=INK)
    axes[0].legend(loc="upper right", frameon=False, labelcolor=INK)

    fig.suptitle("CS error against UWB by distance (static runs)", x=0.01, ha="left", color=INK, fontsize=13)
    path = save(fig, out_dir, "figure_a_static_error.png")
    plt.close(fig)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=Path("figures"))
    args = parser.parse_args()

    stats = scenario_stats(args.data)
    print(stats.round(2).to_string(index=False))
    print(f"\ntotal samples: {stats['n'].sum()}\n")
    combined = combine_rates(stats)
    print(combined.round(2).to_string(index=False))
    print(f"\nsaved {plot(combined, args.out)}")


if __name__ == "__main__":
    main()
