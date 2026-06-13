#!/usr/bin/env python3

import argparse
import csv
import statistics
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the effective sample rate of an EdgePulse capture."
    )
    parser.add_argument("--input", required=True, type=Path, help="Input CSV path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    timestamps = []

    with args.input.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or "time_ms" not in reader.fieldnames:
            raise SystemExit("Input must contain a time_ms column")

        for row in reader:
            try:
                timestamps.append(float(row["time_ms"]))
            except (TypeError, ValueError):
                continue

    if len(timestamps) < 2:
        raise SystemExit("At least two valid rows are required")

    intervals = [
        current - previous
        for previous, current in zip(timestamps, timestamps[1:])
    ]
    positive_intervals = [interval for interval in intervals if interval > 0]
    duration_ms = timestamps[-1] - timestamps[0]

    if duration_ms <= 0 or not positive_intervals:
        raise SystemExit("time_ms must increase across the capture")

    effective_rate = (len(timestamps) - 1) * 1000.0 / duration_ms
    median_interval = statistics.median(positive_intervals)
    median_rate = 1000.0 / median_interval
    non_increasing = len(intervals) - len(positive_intervals)

    print(f"Rows: {len(timestamps)}")
    print(f"Duration: {duration_ms / 1000.0:.2f} s")
    print(f"Effective sample rate: {effective_rate:.2f} Hz")
    print(f"Median interval: {median_interval:.2f} ms ({median_rate:.2f} Hz)")
    print(f"Non-increasing intervals: {non_increasing}")


if __name__ == "__main__":
    main()
