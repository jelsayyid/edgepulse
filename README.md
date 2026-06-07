# EdgePulse

EdgePulse is an initial embedded testbed for adaptive physiological sensing. The first milestone uses an Arduino Nano 33 BLE Sense Rev2 to stream timestamped accelerometer and gyroscope measurements over USB serial, with laptop-side tools for CSV capture, plotting, and motion labeling. The next milestone combines MAX30102 pulse measurements with synchronized IMU data.

## Hardware Target

- Arduino Nano 33 BLE Sense Rev2
- Built-in BMI270/BMM150 IMU
- USB cable for programming and serial logging
- MAX30102 optical pulse sensor

In Arduino IDE, the board may appear as **Arduino Nano 33 BLE** under **Arduino Mbed OS Nano Boards**.

## Current Milestone

The current milestone is an IMU-only logger that samples at roughly 50 Hz and emits:

```text
time_ms,ax,ay,az,gx,gy,gz,motion_mag
```

## Setup

1. Install Arduino IDE and the **Arduino Mbed OS Nano Boards** package.
2. Install the `Arduino_BMI270_BMM150` library through Arduino Library Manager.
3. Install the SparkFun MAX3010x library for the combined logger.
4. Open the IMU-only or combined sketch under `firmware/`.
5. Select the Arduino Nano 33 BLE board and the correct serial port.
6. Upload the sketch and close Arduino Serial Monitor before using the Python logger.

## Next Milestone

`firmware/edgepulse_combined_logger/edgepulse_combined_logger.ino` reads MAX30102 red and infrared values with synchronized acceleration and gyroscope data at roughly 50 Hz. This combined logger is an initial implementation and has not yet been validated on the target hardware.

Connect MAX30102 `VIN` to `3.3V`, `GND` to `GND`, `SDA` to `SDA/A4`, and `SCL` to `SCL/A5`. Leave `INT`, `RD`, and `IRD` unconnected.

## Python Setup

Create a Python environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

## Capture Serial Data

Replace `COM5` with the board's serial port:

```powershell
python analysis/serial_logger.py --port COM5 --out data/imu_log.csv --duration 60
```

Omit `--duration` to log until `Ctrl+C`.

## Plot Sample Data

The included synthetic sample works without hardware:

```powershell
python analysis/plot_csv.py --input data/sample_imu.csv --out sample_plot.png
python analysis/motion_score.py --input data/sample_imu.csv --out data/sample_imu_scored.csv
```

## Current Limitations

- Hardware behavior and timing have not yet been validated on a physical board.
- Combined MAX30102 and IMU acquisition has not yet been validated on the target hardware.
- CSV transport has no packet framing, retransmission, or clock synchronization.
- Motion thresholds are initial defaults and require experimental calibration.
- Adaptive sensing states are planned but not implemented.
