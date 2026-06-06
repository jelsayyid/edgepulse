# EdgePulse Project Brief

## Focus

EdgePulse explores adaptive physiological sensing on a small embedded platform. The initial scaffold separates sensor acquisition, serial transport, data capture, and offline analysis so each stage can be evaluated independently.

## First Technical Target

Use the Arduino Nano 33 BLE Sense Rev2 built-in IMU to stream timestamped acceleration, gyroscope, and acceleration-magnitude values over USB serial at roughly 50 Hz.

## Evaluation Plan

Collect short recordings with the board still, moving gently, and shaking more strongly. Check sample continuity, timing, signal ranges, motion-score behavior, and output volume before adding optical pulse measurements.

## Outputs

- Arduino IMU logger firmware
- Future combined IMU and MAX30102 scaffold
- Serial-to-CSV capture script
- Plotting and motion-labeling scripts
- Synthetic IMU sample data
- Architecture and evaluation notes

## Next Steps

1. Validate the IMU logger on the target board.
2. Measure effective sample rate and serial timing variation.
3. Add MAX30102 acquisition with a documented library dependency.
4. Develop signal-quality flags for contact and motion artifacts.
5. Evaluate adaptive operating states and power-related tradeoffs.
