#include <Wire.h>
#include <Arduino_BMI270_BMM150.h>
#include "MAX30105.h"
#include <math.h>

MAX30105 particleSensor;

const int PPG_SAMPLE_RATE = 100;
const unsigned long PPG_SAMPLE_INTERVAL_MS = 1000 / PPG_SAMPLE_RATE;

bool imuOk = false;
bool ppgOk = false;
bool ppgClockStarted = false;
unsigned long nextPpgTimeMs = 0;

float ax = 0;
float ay = 0;
float az = 0;
float gx = 0;
float gy = 0;
float gz = 0;

void updateImu() {
  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(ax, ay, az);
  }

  if (IMU.gyroscopeAvailable()) {
    IMU.readGyroscope(gx, gy, gz);
  }
}

void printSample(unsigned long timeMs, uint32_t red, uint32_t ir) {
  float motionMag = sqrt(ax * ax + ay * ay + az * az);

  Serial.print(timeMs);
  Serial.print(",");
  Serial.print(red);
  Serial.print(",");
  Serial.print(ir);
  Serial.print(",");
  Serial.print(ax, 6);
  Serial.print(",");
  Serial.print(ay, 6);
  Serial.print(",");
  Serial.print(az, 6);
  Serial.print(",");
  Serial.print(gx, 6);
  Serial.print(",");
  Serial.print(gy, 6);
  Serial.print(",");
  Serial.print(gz, 6);
  Serial.print(",");
  Serial.println(motionMag, 6);
}

void setup() {
  Serial.begin(115200);

  unsigned long start = millis();
  while (!Serial && millis() - start < 3000) {}

  Wire.begin();

  imuOk = IMU.begin();
  if (!imuOk) {
    Serial.println("IMU_INIT_FAILED");
  }

  ppgOk = particleSensor.begin(Wire, I2C_SPEED_STANDARD);
  if (!ppgOk) {
    Serial.println("MAX30102_INIT_FAILED");
  } else {
    byte ledBrightness = 0x1F;
    byte sampleAverage = 1;
    byte ledMode = 2;
    int sampleRate = PPG_SAMPLE_RATE;
    int pulseWidth = 411;
    int adcRange = 4096;

    particleSensor.setup(
      ledBrightness,
      sampleAverage,
      ledMode,
      sampleRate,
      pulseWidth,
      adcRange
    );
  }

  if (imuOk && ppgOk) {
    Serial.println("time_ms,ppg_red,ppg_ir,ax,ay,az,gx,gy,gz,motion_mag");
  }
}

void loop() {
  if (!imuOk || !ppgOk) {
    delay(1000);
    return;
  }

  updateImu();

  uint16_t fetchedSamples = particleSensor.check();
  uint8_t availableSamples = particleSensor.available();

  if (!ppgClockStarted && availableSamples > 0) {
    nextPpgTimeMs =
      millis() - (availableSamples - 1) * PPG_SAMPLE_INTERVAL_MS;
    ppgClockStarted = true;
  } else if (ppgClockStarted && fetchedSamples > availableSamples) {
    nextPpgTimeMs +=
      (fetchedSamples - availableSamples) * PPG_SAMPLE_INTERVAL_MS;
  }

  while (particleSensor.available()) {
    updateImu();

    uint32_t red = particleSensor.getFIFORed();
    uint32_t ir = particleSensor.getFIFOIR();
    printSample(nextPpgTimeMs, red, ir);

    nextPpgTimeMs += PPG_SAMPLE_INTERVAL_MS;
    particleSensor.nextSample();
  }
}
