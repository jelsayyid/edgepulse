#!/usr/bin/env python3

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add rolling motion labels to CSV data.")
    parser.add_argument("--input", required=True, type=Path, help="Input CSV path.")
    parser.add_argument("--out", required=True, type=Path, help="Output CSV path.")
    parser.add_argument("--window", type=int, default=25, help="Rolling window size.")
    parser.add_argument(
        "--moving-threshold",
        type=float,
        default=0.05,
        help="Minimum score labeled MOVING.",
    )
    parser.add_argument(
        "--high-threshold",
        type=float,
        default=0.15,
        help="Minimum score labeled HIGH_MOTION.",
    )
    args = parser.parse_args()

    if args.window <= 0:
        parser.error("--window must be positive")
    if args.moving_threshold < 0 or args.high_threshold < 0:
        parser.error("thresholds must be non-negative")
    if args.high_threshold < args.moving_threshold:
        parser.error("--high-threshold must be at least --moving-threshold")

    return args


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.input)

    if "motion_mag" not in data.columns:
        required = {"ax", "ay", "az"}
        if not required.issubset(data.columns):
            raise SystemExit("Input must contain motion_mag or ax, ay, and az")
        data["motion_mag"] = np.sqrt(
            data["ax"] ** 2 + data["ay"] ** 2 + data["az"] ** 2
        )

    data["motion_score"] = (
        data["motion_mag"]
        .rolling(window=args.window, min_periods=2)
        .std()
        .fillna(0.0)
    )

    data["motion_label"] = np.select(
        [
            data["motion_score"] >= args.high_threshold,
            data["motion_score"] >= args.moving_threshold,
        ],
        ["HIGH_MOTION", "MOVING"],
        default="STILL",
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.out, index=False)
    print(f"Saved {len(data)} labeled rows to {args.out}")


if __name__ == "__main__":
    main()
