# EdgePulse

EdgePulse is an initial embedded testbed for adaptive physiological sensing. The first milestone uses an Arduino Nano 33 BLE Sense Rev2 to stream timestamped accelerometer and gyroscope measurements over USB serial, with laptop-side tools for CSV capture, plotting, and motion labeling. A MAX30102 optical pulse sensor and adaptive sensing policies are planned for later milestones.

## Hardware Target

- Arduino Nano 33 BLE Sense Rev2
- Built-in BMI270/BMM150 IMU
- USB cable for programming and serial logging
- MAX30102 optical pulse sensor (planned)

In Arduino IDE, the board may appear as **Arduino Nano 33 BLE** under **Arduino Mbed OS Nano Boards**.

## Current Milestone

The current milestone is an IMU-only logger that samples at roughly 50 Hz and emits:

```text
time_ms,ax,ay,az,gx,gy,gz,motion_mag
```

## Setup

1. Install Arduino IDE and the **Arduino Mbed OS Nano Boards** package.
2. Install the `Arduino_BMI270_BMM150` library through Arduino Library Manager.
3. Open `firmware/edgepulse_imu_logger/edgepulse_imu_logger.ino`.
4. Select the Arduino Nano 33 BLE board and the correct serial port.
5. Upload the sketch and close Arduino Serial Monitor before using the Python logger.

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
- MAX30102 acquisition is only represented by dependency-free placeholders.
- CSV transport has no packet framing, retransmission, or clock synchronization.
- Motion thresholds are initial defaults and require experimental calibration.
- Adaptive sensing states are planned but not implemented.
