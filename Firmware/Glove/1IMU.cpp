#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>

/* Assign a unique ID to this sensor at the same time */
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);
#define cs1 2;
#define cs2 3;


float AccelMinX = 0;
float AccelMaxX = 0;
float AccelMinY = 0;
float AccelMaxY = 0;
float AccelMinZ = 0;
float AccelMaxZ = 0;


void setup(void) 
{
  Serial.begin(9600);
  Serial.println("ADXL345 Accelerometer Calibration"); 
  Serial.println("");
  
  /* Initialise the sensor */
  if(!accel.begin())
  {
    /* There was a problem detecting the ADXL345 ... check your connections */
    Serial.println("Ooops, no ADXL345 detected ... Check your wiring!");
    while(1);
  }
}

void loop(void)
{
    sensors_event_t accelEvent;  
    accel.getEvent(&accelEvent);

    Serial.print("X: ");
    Serial.print(accelEvent.acceleration.x);
    Serial.print("  Y: ");
    Serial.print(accelEvent.acceleration.x);
    Serial.print("  Z: ");
    Serial.println(accelEvent.acceleration.x);

    delay(50);
    
    while (Serial.available())
    {
      Serial.read();  // clear the input buffer
    }
}