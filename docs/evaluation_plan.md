# Evaluation Plan

## First Experiments

Record separate IMU sessions under three controlled conditions:

1. Board resting still on a stable surface
2. Gentle hand movement and orientation changes
3. Stronger repeated shaking

Compare the raw axes, acceleration magnitude, rolling motion score, and resulting labels. Note dropped or malformed rows and estimate the effective sample interval from `time_ms`.

## Later Pulse Experiments

After MAX30102 integration, collect:

1. Clean finger pulse with stable contact
2. Poor or intermittent finger contact
3. Pulse data corrupted by deliberate motion

Use the synchronized IMU measurements to examine whether motion explains optical signal degradation.

## Metrics

- Valid sample count
- Missing, malformed, duplicate, or irregularly timed samples
- Rolling motion score and label distribution
- Logging volume in bytes per second
- End-to-end latency estimate
- Optical quality flags once implemented

Hardware results should be reported only after measurements are collected on the target setup.
