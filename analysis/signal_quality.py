#!/usr/bin/env python3

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {
    "time_ms",
    "ppg_red",
    "ppg_ir",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add signal-quality labels to combined PPG and IMU data."
    )
    parser.add_argument("--input", required=True, type=Path, help="Input CSV path.")
    parser.add_argument("--out", required=True, type=Path, help="Output CSV path.")
    parser.add_argument("--window", type=int, default=25, help="Rolling window size.")
    parser.add_argument(
        "--finger-threshold",
        type=float,
        default=10000,
        help="Minimum IR value indicating finger contact.",
    )
    parser.add_argument(
        "--noise-threshold",
        type=float,
        default=0.08,
        help="Maximum clean PPG noise score.",
    )
    parser.add_argument(
        "--motion-threshold",
        type=float,
        default=0.01,
        help="Maximum clean motion score.",
    )
    parser.add_argument(
        "--phase-labels",
        help="Known elapsed-time phases, for example 0:NO_FINGER,15:CLEAN.",
    )
    parser.add_argument(
        "--protocol",
        type=Path,
        help="Optional capture protocol CSV.",
    )
    parser.add_argument(
        "--min-segment-s",
        type=float,
        default=2.0,
        help="Minimum automatic CLEAN or NOISY segment duration.",
    )
    args = parser.parse_args()

    if args.window <= 0:
        parser.error("--window must be positive")
    if args.finger_threshold < 0:
        parser.error("--finger-threshold must be non-negative")
    if args.noise_threshold < 0 or args.motion_threshold < 0:
        parser.error("quality thresholds must be non-negative")
    if args.min_segment_s < 0:
        parser.error("--min-segment-s must be non-negative")
    if args.protocol and args.phase_labels:
        parser.error("--protocol and --phase-labels cannot be used together")

    return args


def parse_phase_labels(value: str) -> list[tuple[float, str]]:
    allowed = {"NO_FINGER", "CLEAN", "NOISY"}
    phases = []

    for item in value.split(","):
        try:
            start_text, label = item.strip().split(":", maxsplit=1)
            start = float(start_text)
        except ValueError as exc:
            raise SystemExit("Invalid --phase-labels format") from exc
        if start < 0 or label not in allowed:
            raise SystemExit("Invalid --phase-labels value")
        phases.append((start, label))

    phases.sort()
    if not phases or phases[0][0] != 0:
        raise SystemExit("--phase-labels must begin at 0 seconds")
    return phases


def capture_name(path: Path) -> str:
    name = path.stem
    for suffix in ("_labeled", "_pulse"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def load_protocol_labels(
    protocol_path: Path,
    input_path: Path,
    elapsed_s: pd.Series,
) -> pd.Series:
    protocol = pd.read_csv(protocol_path)
    required = {
        "capture",
        "interval_start_s",
        "interval_end_s",
        "label",
        "notes",
    }
    missing = required.difference(protocol.columns)
    if missing:
        raise SystemExit(
            f"Protocol file missing columns: {', '.join(sorted(missing))}"
        )

    annotations = protocol.loc[
        protocol["capture"] == capture_name(input_path)
    ].copy()
    if annotations.empty:
        raise SystemExit("No protocol annotations found for input capture")

    allowed = {"NO_FINGER", "CLEAN", "NOISY"}
    invalid = sorted(set(annotations["label"]) - allowed)
    if invalid:
        raise SystemExit(f"Unsupported protocol labels: {', '.join(invalid)}")

    labels = pd.Series(pd.NA, index=elapsed_s.index, dtype="object")
    for row in annotations.itertuples(index=False):
        start = float(row.interval_start_s)
        end = float(row.interval_end_s)
        if end <= start:
            raise SystemExit("Protocol intervals must have positive duration")
        labels.loc[(elapsed_s >= start) & (elapsed_s < end)] = row.label
    return labels


def label_segments(labels: np.ndarray) -> list[tuple[int, int, str]]:
    if len(labels) == 0:
        return []

    segments = []
    start = 0
    for index in range(1, len(labels) + 1):
        if index == len(labels) or labels[index] != labels[start]:
            segments.append((start, index - 1, labels[start]))
            start = index
    return segments


def smooth_automatic_labels(
    labels: np.ndarray,
    elapsed_s: np.ndarray,
    slope_score: np.ndarray,
    min_segment_s: float,
    noise_threshold: float,
) -> np.ndarray:
    smoothed = labels.copy()
    sample_duration = (
        float(np.median(np.diff(elapsed_s))) if len(elapsed_s) > 1 else 0.0
    )

    for _ in range(3):
        changed = False
        segments = label_segments(smoothed)
        for position in range(1, len(segments) - 1):
            start, end, label = segments[position]
            previous_label = segments[position - 1][2]
            next_label = segments[position + 1][2]
            duration = elapsed_s[end] - elapsed_s[start] + sample_duration
            if duration >= min_segment_s:
                continue

            if label == "CLEAN" and (
                previous_label == "NOISY" or next_label == "NOISY"
            ):
                smoothed[start : end + 1] = "NOISY"
                changed = True
            elif (
                label == "NOISY"
                and previous_label == "CLEAN"
                and next_label == "CLEAN"
            ):
                large_slope = np.max(slope_score[start : end + 1])
                if large_slope <= noise_threshold * 2:
                    smoothed[start : end + 1] = "CLEAN"
                    changed = True
        if not changed:
            break

    return smoothed


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.input)

    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {', '.join(sorted(missing))}")

    finger_detected = data["ppg_ir"] >= args.finger_threshold
    ir_mean = data["ppg_ir"].rolling(
        window=args.window, center=True, min_periods=1
    ).mean()
    red_mean = data["ppg_red"].rolling(
        window=args.window, center=True, min_periods=1
    ).mean()
    data["ppg_ir_detrended"] = data["ppg_ir"] - ir_mean
    data["ppg_red_detrended"] = data["ppg_red"] - red_mean

    finger_ir = data["ppg_ir"].where(finger_detected)
    rolling_ir = finger_ir.rolling(window=args.window, min_periods=2)

    rolling_mean = rolling_ir.mean()
    rolling_std = rolling_ir.std()
    data["ppg_noise_score"] = (rolling_std / rolling_mean).fillna(0.0)
    data["slope_score"] = (
        (finger_ir.diff().abs() / rolling_mean)
        .fillna(0.0)
        .rolling(window=3, min_periods=1)
        .max()
    )

    if "motion_mag" in data.columns:
        motion_mean = data["motion_mag"].rolling(
            window=args.window, center=True, min_periods=1
        ).mean()
        data["dynamic_motion"] = (data["motion_mag"] - motion_mean).abs()
        data["motion_score"] = (
            data["dynamic_motion"]
            .rolling(window=args.window, min_periods=1)
            .mean()
            .fillna(0.0)
        )
    else:
        data["dynamic_motion"] = 0.0
        data["motion_score"] = 0.0

    noisy = finger_detected & (
        (data["ppg_noise_score"] > args.noise_threshold)
        | (data["slope_score"] > args.noise_threshold)
        | (data["dynamic_motion"] > args.motion_threshold)
    )
    automatic_labels = np.select(
        [~finger_detected, noisy],
        ["NO_FINGER", "NOISY"],
        default="CLEAN",
    )
    elapsed_s = (data["time_ms"] - data["time_ms"].iloc[0]) / 1000.0
    data["signal_label"] = smooth_automatic_labels(
        automatic_labels,
        elapsed_s.to_numpy(dtype=float),
        data["slope_score"].to_numpy(dtype=float),
        args.min_segment_s,
        args.noise_threshold,
    )

    if args.protocol:
        data["protocol_label"] = load_protocol_labels(
            args.protocol,
            args.input,
            elapsed_s,
        )
        data["signal_label"] = data["protocol_label"].fillna(data["signal_label"])
    elif args.phase_labels:
        phases = parse_phase_labels(args.phase_labels)
        for start, label in phases:
            data.loc[elapsed_s >= start, "signal_label"] = label

    args.out.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.out, index=False)

    counts = data["signal_label"].value_counts()
    row_count = len(data)
    print(f"Rows: {row_count}")
    for label in ("NO_FINGER", "CLEAN", "NOISY"):
        percentage = 100.0 * counts.get(label, 0) / row_count if row_count else 0.0
        print(f"{label}: {percentage:.1f}%")


if __name__ == "__main__":
    main()
