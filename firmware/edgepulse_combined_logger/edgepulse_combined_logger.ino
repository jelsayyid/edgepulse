#include <Arduino_BMI270_BMM150.h>
#include <math.h>

const unsigned long SAMPLE_INTERVAL_MS = 20;
const unsigned long SERIAL_WAIT_MS = 2000;

unsigned long nextSampleMs = 0;

void setup() {
  Serial.begin(115200);

  unsigned long waitStart = millis();
  while (!Serial && millis() - waitStart < SERIAL_WAIT_MS) {
  }

  if (!IMU.begin()) {
    Serial.println("ERROR: IMU initialization failed");
    while (true) {
      delay(1000);
    }
  }

  // TODO: Initialize the MAX30102 after selecting a sensor library.
  Serial.println("time_ms,ppg_red,ppg_ir,ax,ay,az,gx,gy,gz,motion_mag,quality_flag");
  nextSampleMs = millis();
}

void loop() {
  unsigned long now = millis();
  if ((long)(now - nextSampleMs) < 0) {
    return;
  }

  if (!IMU.accelerationAvailable() || !IMU.gyroscopeAvailable()) {
    return;
  }

  float ax;
  float ay;
  float az;
  float gx;
  float gy;
  float gz;

  IMU.readAcceleration(ax, ay, az);
  IMU.readGyroscope(gx, gy, gz);

  float motionMag = sqrt(ax * ax + ay * ay + az * az);

  // TODO: Replace placeholders with MAX30102 samples and a derived quality flag.
  unsigned long ppgRed = 0;
  unsigned long ppgIr = 0;
  int qualityFlag = 0;

  Serial.print(now);
  Serial.print(',');
  Serial.print(ppgRed);
  Serial.print(',');
  Serial.print(ppgIr);
  Serial.print(',');
  Serial.print(ax, 6);
  Serial.print(',');
  Serial.print(ay, 6);
  Serial.print(',');
  Serial.print(az, 6);
  Serial.print(',');
  Serial.print(gx, 6);
  Serial.print(',');
  Serial.print(gy, 6);
  Serial.print(',');
  Serial.print(gz, 6);
  Serial.print(',');
  Serial.print(motionMag, 6);
  Serial.print(',');
  Serial.println(qualityFlag);

  nextSampleMs = now + SAMPLE_INTERVAL_MS;
}
