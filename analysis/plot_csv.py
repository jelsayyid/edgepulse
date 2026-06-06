#!/usr/bin/env python3

import argparse
import os
import tempfile
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "edgepulse-matplotlib"),
)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot EdgePulse CSV data.")
    parser.add_argument("--input", required=True, type=Path, help="Input CSV path.")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("plot.png"),
        help="Output PNG path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.input)

    plot_groups = []
    if {"ax", "ay", "az"}.issubset(data.columns):
        plot_groups.append(("Acceleration", ["ax", "ay", "az"], "Acceleration (g)"))
    if "motion_mag" in data.columns:
        plot_groups.append(("Motion magnitude", ["motion_mag"], "Magnitude (g)"))

    ppg_columns = [name for name in ("ppg_red", "ppg_ir") if name in data.columns]
    if ppg_columns:
        plot_groups.append(("Optical pulse", ppg_columns, "Sensor value"))

    if not plot_groups:
        raise SystemExit("No supported signal columns found in the input CSV")

    if "time_ms" in data.columns:
        x = data["time_ms"] / 1000.0
        x_label = "Time (s)"
    else:
        x = data.index
        x_label = "Sample"

    figure, axes = plt.subplots(
        len(plot_groups),
        1,
        figsize=(10, 3.2 * len(plot_groups)),
        sharex=True,
        squeeze=False,
    )

    for axis, (title, columns, y_label) in zip(axes[:, 0], plot_groups):
        for column in columns:
            axis.plot(x, data[column], label=column)
        axis.set_title(title)
        axis.set_ylabel(y_label)
        axis.grid(True, alpha=0.3)
        axis.legend()

    axes[-1, 0].set_xlabel(x_label)
    figure.tight_layout()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.out, dpi=150)
    plt.close(figure)
    print(f"Saved plot to {args.out}")


if __name__ == "__main__":
    main()
