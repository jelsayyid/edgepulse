#!/usr/bin/env python3

import argparse
import time
from pathlib import Path

import serial


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Save serial CSV data to a file.")
    parser.add_argument("--port", required=True, help="Serial port, for example COM5.")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate.")
    parser.add_argument("--out", required=True, type=Path, help="Output CSV path.")
    parser.add_argument(
        "--duration",
        type=float,
        help="Optional logging duration in seconds.",
    )
    parser.add_argument(
        "--header",
        help="Optional CSV header written before serial data.",
    )
    args = parser.parse_args()

    if args.baud <= 0:
        parser.error("--baud must be positive")
    if args.duration is not None and args.duration <= 0:
        parser.error("--duration must be positive")

    return args


def main() -> None:
    args = parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Opening {args.port} at {args.baud} baud")
    line_count = 0
    start_time = time.monotonic()

    try:
        with serial.Serial(args.port, args.baud, timeout=1) as port:
            with args.out.open("wb") as output:
                print(f"Logging to {args.out}")
                if args.header is not None:
                    output.write(args.header.rstrip("\r\n").encode("utf-8") + b"\n")
                    output.flush()

                try:
                    while True:
                        if (
                            args.duration is not None
                            and time.monotonic() - start_time >= args.duration
                        ):
                            break

                        raw_line = port.readline()
                        csv_line = raw_line.rstrip(b"\r\n")
                        if not csv_line:
                            continue

                        output.write(csv_line + b"\n")
                        output.flush()
                        line_count += 1
                except KeyboardInterrupt:
                    print("\nStopping on Ctrl+C")
    except serial.SerialException as exc:
        raise SystemExit(f"Serial error: {exc}") from exc
    except OSError as exc:
        raise SystemExit(f"File error: {exc}") from exc

    elapsed = time.monotonic() - start_time
    print(f"Saved {line_count} lines in {elapsed:.1f} seconds")


if __name__ == "__main__":
    main()
