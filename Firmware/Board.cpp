#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>

Adafruit_ADXL345_Unified accel1 = Adafruit_ADXL345_Unified(0x53);

void setup(void) {
  Serial.begin(9600);

  if (!accel1.begin()) {
    while (1);
  }

}

void loop(void) {
  sensors_event_t event1;

  accel1.getEvent(&event1);

  int slider1 = analogRead(A0);
  int slider2 = analogRead(A1);
  int slider3 = analogRead(A2);
  int slider4 = analogRead(A3);

  Serial.print(event1.acceleration.x); Serial.print(",");
  Serial.print(event1.acceleration.y); Serial.print(",");
  Serial.print(event1.acceleration.z); Serial.print(",");

  Serial.print(slider1); Serial.print(",");
  Serial.print(slider2); Serial.print(",");
  Serial.print(slider3); Serial.print(",")
  Serial.println(slider4);

}
