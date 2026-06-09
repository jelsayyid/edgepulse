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
    args = parser.parse_args()

    if args.window <= 0:
        parser.error("--window must be positive")
    if args.finger_threshold < 0:
        parser.error("--finger-threshold must be non-negative")
    if args.noise_threshold < 0 or args.motion_threshold < 0:
        parser.error("quality thresholds must be non-negative")

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


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.input)

    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {', '.join(sorted(missing))}")

    finger_detected = data["ppg_ir"] >= args.finger_threshold
    finger_ir = data["ppg_ir"].where(finger_detected)
    rolling_ir = finger_ir.rolling(window=args.window, min_periods=2)

    rolling_mean = rolling_ir.mean()
    rolling_std = rolling_ir.std()
    rolling_variation = (rolling_std / rolling_mean).fillna(0.0)
    sudden_change = (finger_ir.diff().abs() / rolling_mean).fillna(0.0)
    sudden_change = sudden_change.rolling(window=3, min_periods=1).max()
    data["ppg_noise_score"] = pd.concat(
        [rolling_variation, sudden_change], axis=1
    ).max(axis=1)

    if "motion_mag" in data.columns:
        motion_mean = data["motion_mag"].rolling(
            window=args.window, min_periods=1
        ).mean()
        data["dynamic_motion"] = (data["motion_mag"] - motion_mean).abs()
        data["motion_score"] = (
            data["dynamic_motion"]
            .rolling(window=args.window, min_periods=2)
            .std()
            .fillna(0.0)
        )
    else:
        data["motion_score"] = 0.0

    noisy = finger_detected & (
        (data["ppg_noise_score"] > args.noise_threshold)
        | (data["motion_score"] > args.motion_threshold)
    )
    data["signal_label"] = np.select(
        [~finger_detected, noisy],
        ["NO_FINGER", "NOISY"],
        default="CLEAN",
    )

    if args.phase_labels:
        phases = parse_phase_labels(args.phase_labels)
        elapsed_s = (data["time_ms"] - data["time_ms"].iloc[0]) / 1000.0
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
