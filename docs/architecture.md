# Architecture

## Current Data Path

1. The Arduino Nano 33 BLE Sense Rev2 reads acceleration and gyroscope data from its built-in IMU.
2. Firmware adds a `millis()` timestamp and acceleration magnitude.
3. The Arduino streams CSV rows over USB serial at 115200 baud.
4. A laptop runs `analysis/serial_logger.py` to save the rows to a CSV file.
5. Python tools plot the signals and compute rolling motion labels.

```text
Built-in IMU -> Arduino firmware -> USB serial -> CSV file -> Python analysis
```

## Next Milestone

The combined logger uses the SparkFun MAX3010x library to read MAX30102 red and infrared measurements alongside the IMU fields:

```text
time_ms,ppg_red,ppg_ir,ax,ay,az,gx,gy,gz,motion_mag
```

This is the next PPG + IMU serial logging milestone. The implementation has not yet been validated on the target hardware, and signal-quality logic remains planned work.

## Planned Adaptive Policy

Later analysis will classify time windows into operating states:

- `NORMAL`: stable signal and standard acquisition
- `NOISY`: degraded signal quality
- `WATCH`: elevated monitoring without full event capture
- `LOW_POWER`: reduced activity when conditions permit
- `EVENT_CAPTURE`: high-detail capture around a detected event

These states are architectural targets, not current firmware behavior.
