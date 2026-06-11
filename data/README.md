# Data

`sample_imu.csv` is synthetic input for testing the analysis scripts without hardware.

`combined_contact_motion_001.csv` is the first real combined PPG + IMU hardware capture. Its four 15-second phases are no finger, still finger, deliberate motion/contact artifact, and still-finger recovery.

`capture_protocols.csv` records the known phases for controlled captures. For `combined_contact_motion_001`, the 30-45 second interval is known contact artifact from intentional finger tapping.

`combined_contact_motion_001_labeled.csv` adds protocol-aligned `NO_FINGER`, `CLEAN`, and `NOISY` signal-quality labels.

`ppg_red` and `ppg_ir` are raw optical sensor counts, not heart rate. BPM is estimated later from clean intervals in the detrended infrared waveform.

`motion_mag` includes gravity and remains near 1 g while the board is still. `dynamic_motion` measures change relative to a rolling baseline and better reflects movement.

Do not treat the synthetic values as measured hardware performance.
