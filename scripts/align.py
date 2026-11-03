"""Load a scenario's CS and UWB logs and align them in time (README section 2)."""
from pathlib import Path

import pandas as pd

TOLERANCE = pd.Timedelta("500ms")


def load_cs(data_dir, scenario):
    cs = pd.read_csv(Path(data_dir) / "RangingFilter" / f"{scenario}.csv")
    cs["t"] = pd.to_datetime(cs["Timestamp"], format="%m/%d/%Y %H:%M:%S.%f")
    return cs.sort_values("t")


def load_gt(data_dir, scenario):
    gt = pd.read_csv(Path(data_dir) / "GT" / f"{scenario}.csv")
    gt["t"] = pd.to_datetime(gt["Timestamp"])
    return gt.sort_values("t")


def align(data_dir, scenario):
    """Pair each CS sample with the nearest UWB sample within 500 ms.

    Returns only paired rows, with `err` = CS - UWB in metres.
    """
    cs = load_cs(data_dir, scenario)
    gt = load_gt(data_dir, scenario)
    m = pd.merge_asof(cs, gt[["t", "Distance(m)"]], on="t",
                      direction="nearest", tolerance=TOLERANCE)
    m = m.dropna(subset=["Distance(m)"]).copy()
    m["err"] = m["Distance (m)"] - m["Distance(m)"]
    return m
