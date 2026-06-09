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
import numpy as np
import pandas as pd

try:
    from scipy.signal import find_peaks as scipy_find_peaks
except ImportError:
    scipy_find_peaks = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract pulse peaks from EdgePulse optical data."
    )
    parser.add_argument("--input", required=True, type=Path, help="Input CSV path.")
    parser.add_argument(
        "--out-plot",
        required=True,
        type=Path,
        help="Output plot path.",
    )
    parser.add_argument("--out-csv", type=Path, help="Optional output CSV path.")
    parser.add_argument("--window", type=int, default=25, help="Baseline window size.")
    parser.add_argument(
        "--min-distance-s",
        type=float,
        default=0.4,
        help="Minimum plausible beat spacing in seconds.",
    )
    parser.add_argument(
        "--max-distance-s",
        type=float,
        default=1.5,
        help="Maximum plausible beat spacing in seconds.",
    )
    args = parser.parse_args()

    if args.window <= 0:
        parser.error("--window must be positive")
    if args.min_distance_s <= 0 or args.max_distance_s <= 0:
        parser.error("beat spacing limits must be positive")
    if args.max_distance_s <= args.min_distance_s:
        parser.error("--max-distance-s must exceed --min-distance-s")

    return args


def contiguous_regions(mask: np.ndarray) -> list[tuple[int, int]]:
    regions = []
    start = None

    for index, valid in enumerate(mask):
        if valid and start is None:
            start = index
        if start is not None and (not valid or index == len(mask) - 1):
            end = index if valid and index == len(mask) - 1 else index - 1
            regions.append((start, end))
            start = None

    return regions


def peak_candidates(values: np.ndarray) -> np.ndarray:
    if len(values) < 3:
        return np.array([], dtype=int)

    if scipy_find_peaks is not None:
        prominence = max(float(np.nanstd(values)) * 0.1, np.finfo(float).eps)
        peaks, _ = scipy_find_peaks(values, prominence=prominence)
        return peaks

    return np.array(
        [
            index
            for index in range(1, len(values) - 1)
            if values[index] > values[index - 1]
            and values[index] >= values[index + 1]
        ],
        dtype=int,
    )


def enforce_spacing(
    candidates: list[int],
    times: np.ndarray,
    values: np.ndarray,
    min_distance_s: float,
    max_distance_s: float,
) -> list[int]:
    selected = []
    for index in sorted(candidates, key=lambda item: values[item], reverse=True):
        if all(abs(times[index] - times[other]) >= min_distance_s for other in selected):
            selected.append(index)

    selected.sort()
    return [
        index
        for position, index in enumerate(selected)
        if (
            position > 0
            and times[index] - times[selected[position - 1]] <= max_distance_s
        )
        or (
            position + 1 < len(selected)
            and times[selected[position + 1]] - times[index] <= max_distance_s
        )
    ]


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.input)

    required = {"time_ms", "ppg_ir"}
    missing = required.difference(data.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {', '.join(sorted(missing))}")

    time_s = data["time_ms"].to_numpy(dtype=float) / 1000.0
    if len(time_s) > 1 and np.any(np.diff(time_s) <= 0):
        raise SystemExit("time_ms must be strictly increasing")

    baseline = data["ppg_ir"].rolling(
        window=args.window,
        center=True,
        min_periods=1,
    ).mean()
    data["ppg_ir_detrended"] = data["ppg_ir"] - baseline

    if "signal_label" in data.columns:
        valid_rows = data["signal_label"].eq("CLEAN").to_numpy()
    else:
        valid_rows = np.ones(len(data), dtype=bool)

    detrended = data["ppg_ir_detrended"].to_numpy(dtype=float)
    detected_peaks = []
    interval_by_peak = {}

    for start, end in contiguous_regions(valid_rows):
        local_values = detrended[start : end + 1]
        candidates = (peak_candidates(local_values) + start).tolist()
        region_peaks = enforce_spacing(
            candidates,
            time_s,
            detrended,
            args.min_distance_s,
            args.max_distance_s,
        )
        detected_peaks.extend(region_peaks)

        for previous, current in zip(region_peaks[:-1], region_peaks[1:]):
            interval = time_s[current] - time_s[previous]
            if args.min_distance_s <= interval <= args.max_distance_s:
                interval_by_peak[current] = interval

    detected_peaks = sorted(set(detected_peaks))
    intervals = np.array(list(interval_by_peak.values()), dtype=float)
    median_bpm = 60.0 / np.median(intervals) if len(intervals) else None

    data["pulse_peak"] = 0
    data["beat_interval_s"] = np.nan
    data["instant_bpm"] = np.nan
    if detected_peaks:
        data.loc[detected_peaks, "pulse_peak"] = 1
    for index, interval in interval_by_peak.items():
        data.loc[index, "beat_interval_s"] = interval
        data.loc[index, "instant_bpm"] = 60.0 / interval

    print(f"Detected beats: {len(detected_peaks)}")
    if median_bpm is None:
        print("Estimated median BPM: unavailable")
    else:
        print(f"Estimated median BPM: {median_bpm:.1f}")

    figure, axis = plt.subplots(figsize=(11, 5))
    axis.plot(time_s, detrended, label="ppg_ir_detrended", linewidth=1.2)
    if detected_peaks:
        axis.scatter(
            time_s[detected_peaks],
            detrended[detected_peaks],
            color="#dc2626",
            marker="x",
            s=42,
            label="Detected peak",
            zorder=3,
        )
    axis.axhline(0, color="#6b7280", linewidth=0.8, alpha=0.6)
    axis.set_title(
        "Detrended infrared pulse"
        if median_bpm is None
        else f"Detrended infrared pulse, median {median_bpm:.1f} BPM"
    )
    axis.set_xlabel("Time (s)")
    axis.set_ylabel("Detrended IR value")
    axis.grid(True, alpha=0.3)
    axis.legend()
    figure.tight_layout()

    args.out_plot.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.out_plot, dpi=150)
    plt.close(figure)
    print(f"Saved plot to {args.out_plot}")

    if args.out_csv is not None:
        args.out_csv.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(args.out_csv, index=False)
        print(f"Saved pulse data to {args.out_csv}")


if __name__ == "__main__":
    main()
