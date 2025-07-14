//Packet [x1, y1, z1, x2, y2, z2, s1, s2, s3, s4]


#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>

Adafruit_ADXL345_Unified accel1 = Adafruit_ADXL345_Unified(1);
Adafruit_ADXL345_Unified accel2 = Adafruit_ADXL345_Unified(2);

#define IMU1_ADDRESS 0x53
#define IMU2_ADDRESS 0x1D

void setup(void) 
{
  Serial.begin(9600);

  if (!accel1.begin(IMU1_ADDRESS)) {
    Serial.println("No ADXL345 at 0x53");
    while (1);
  }

  if (!accel2.begin(IMU2_ADDRESS)) {
    Serial.println("No ADXL345 at 0x1D");
    while (1);
  }
}

void loop(void)
{
  sensors_event_t event1, event2;

  accel1.getEvent(&event1);
  accel2.getEvent(&event2);

  int slider1 = analogRead(A0);
  int slider2 = analogRead(A1);
  int slider3 = analogRead(A2);
  int slider4 = analogRead(A3);

  Serial.print(event1.acceleration.x); Serial.print(",");
  Serial.print(event1.acceleration.y); Serial.print(",");
  Serial.print(event1.acceleration.z); Serial.print(",");
  Serial.print(event2.acceleration.x); Serial.print(",");
  Serial.print(event2.acceleration.y); Serial.print(",");
  Serial.print(event2.acceleration.z); Serial.print(",");
  Serial.print(slider1); Serial.print(",");
  Serial.print(slider2); Serial.print(",");
  Serial.print(slider3); Serial.print(",");
  Serial.println(slider4);

  delay(200);
}
