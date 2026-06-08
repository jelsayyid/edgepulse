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
from matplotlib.patches import Patch
import pandas as pd


SIGNAL_COLORS = {
    "NO_FINGER": "#9ca3af",
    "CLEAN": "#22c55e",
    "NOISY": "#ef4444",
}


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


def shade_signal_regions(axis, x, labels) -> None:
    if labels.empty:
        return

    unknown = sorted(set(labels.dropna()) - set(SIGNAL_COLORS))
    if unknown:
        raise SystemExit(f"Unsupported signal labels: {', '.join(unknown)}")

    x_values = list(x)
    if len(x_values) == 1:
        boundaries = [x_values[0] - 0.5, x_values[0] + 0.5]
    else:
        midpoints = [
            (left + right) / 2
            for left, right in zip(x_values[:-1], x_values[1:])
        ]
        boundaries = [
            x_values[0] - (x_values[1] - x_values[0]) / 2,
            *midpoints,
            x_values[-1] + (x_values[-1] - x_values[-2]) / 2,
        ]

    start_index = 0
    label_values = list(labels)
    for index in range(1, len(label_values) + 1):
        if index == len(label_values) or label_values[index] != label_values[start_index]:
            label = label_values[start_index]
            if label in SIGNAL_COLORS:
                axis.axvspan(
                    boundaries[start_index],
                    boundaries[index],
                    color=SIGNAL_COLORS[label],
                    alpha=0.14,
                )
            start_index = index

    quality_handles = [
        Patch(facecolor=color, alpha=0.25, label=label)
        for label, color in SIGNAL_COLORS.items()
    ]
    signal_legend = axis.legend(loc="upper left")
    axis.add_artist(signal_legend)
    axis.legend(
        handles=quality_handles,
        title="Signal quality",
        loc="upper right",
    )


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.input)

    plot_groups = []
    ppg_columns = [name for name in ("ppg_red", "ppg_ir") if name in data.columns]
    if ppg_columns:
        plot_groups.append(("Optical pulse", ppg_columns, "Sensor value", 4.0))

    if "dynamic_motion" in data.columns:
        plot_groups.append(
            ("Dynamic motion", ["dynamic_motion"], "Deviation (g)", 2.0)
        )
    elif "motion_score" in data.columns:
        plot_groups.append(
            ("Motion score", ["motion_score"], "Motion score", 2.0)
        )
    elif "motion_mag" in data.columns:
        plot_groups.append(
            ("Motion magnitude", ["motion_mag"], "Magnitude (g)", 2.0)
        )

    if {"ax", "ay", "az"}.issubset(data.columns):
        plot_groups.append(
            ("Acceleration", ["ax", "ay", "az"], "Acceleration (g)", 1.8)
        )

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
        gridspec_kw={"height_ratios": [group[3] for group in plot_groups]},
    )

    for axis, (title, columns, y_label, _) in zip(axes[:, 0], plot_groups):
        for column in columns:
            axis.plot(x, data[column], label=column)
        axis.set_title(title)
        axis.set_ylabel(y_label)
        axis.grid(True, alpha=0.3)
        axis.legend()

    if ppg_columns and "signal_label" in data.columns:
        shade_signal_regions(axes[0, 0], x, data["signal_label"])

    axes[-1, 0].set_xlabel(x_label)
    figure.tight_layout()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.out, dpi=150)
    plt.close(figure)
    print(f"Saved plot to {args.out}")


if __name__ == "__main__":
    main()
