# Data

`sample_imu.csv` is synthetic input for testing the analysis scripts without hardware.

`combined_contact_motion_001.csv` is the first real combined PPG + IMU hardware capture. Its four 15-second phases are no finger, still finger, deliberate motion/contact artifact, and still-finger recovery.

`combined_contact_motion_001_labeled.csv` adds phase-aligned `NO_FINGER`, `CLEAN`, and `NOISY` signal-quality labels.

Do not treat the synthetic values as measured hardware performance.
