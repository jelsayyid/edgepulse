#include <Wire.h>
#include <Arduino_BMI270_BMM150.h>
#include "MAX30105.h"
#include <math.h>

MAX30105 particleSensor;

const unsigned long SAMPLE_INTERVAL_MS = 20;
unsigned long lastSample = 0;

bool imuOk = false;
bool ppgOk = false;

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
    byte sampleAverage = 4;
    byte ledMode = 2;
    int sampleRate = 50;
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

  if (millis() - lastSample < SAMPLE_INTERVAL_MS) {
    return;
  }
  lastSample = millis();

  long red = particleSensor.getRed();
  long ir = particleSensor.getIR();

  float ax = 0, ay = 0, az = 0;
  float gx = 0, gy = 0, gz = 0;

  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(ax, ay, az);
  }

  if (IMU.gyroscopeAvailable()) {
    IMU.readGyroscope(gx, gy, gz);
  }

  float motionMag = sqrt(ax * ax + ay * ay + az * az);

  Serial.print(millis());
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
