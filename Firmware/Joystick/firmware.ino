#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <SPI.h>
#include "ibus.h"

#define INTERNAL_LED 2

#define X 39
#define Y 36
#define Z 4

#define TFT_CS 5
#define TFT_DC 17

byte analogPins[] = {39, 36};
byte digitalPins[] = {4};
byte digitalBitmappedPins[] = {};

#define ANALOG_REFERENCE DEFAULT
#define ANALOG_INPUTS_COUNT sizeof(analogPins)
#define DIGITAL_INPUTS_COUNT sizeof(digitalPins)
#define DIGITAL_BITMAPPED_INPUTS_COUNT sizeof(digitalBitmappedPins)
#define NUM_CHANNELS ( (ANALOG_INPUTS_COUNT) + (DIGITAL_INPUTS_COUNT) + (15 + (DIGITAL_BITMAPPED_INPUTS_COUNT))/16 )

Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, -1);
IBus ibus(NUM_CHANNELS);

unsigned long lastDisplayUpdate = 0;
unsigned long prevHours = 999, prevMinutes = 999, prevSeconds = 999;

int lastState = LOW;
int currentState;

int lastDotX = 80, lastDotY = 100;
int gridCentreX = 80, gridCentreY = 92;
int gridSize = 25;

void setup() {
  pinMode(INTERNAL_LED, OUTPUT);
  pinMode(Z, INPUT_PULLUP);
  Serial.begin(115200);

  tft.initR(INITR_BLACKTAB);  
  tft.fillScreen(ST77XX_BLACK);
  tft.setRotation(3);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(10, 10);
  tft.println("meow :3");
  drawJoystickGrid();
}

void drawJoystickGrid() {
  tft.drawLine(gridCentreX - gridSize, gridCentreY, gridCentreX + gridSize, gridCentreY, ST77XX_WHITE);
  tft.drawLine(gridCentreX, gridCentreY - gridSize, gridCentreX, gridCentreY + gridSize, ST77XX_WHITE);
  tft.drawCircle(gridCentreX, gridCentreY, gridSize, ST77XX_WHITE);
}

void loop() {
  unsigned long currentTime = millis();

  if (currentTime - lastDisplayUpdate >= 1000) {
    unsigned long seconds = currentTime / 1000;
    unsigned long minutes = seconds / 60;
    unsigned long hours = minutes / 60;
    
    seconds = seconds % 60;
    minutes = minutes % 60;
    
    if (hours != prevHours || minutes != prevMinutes || seconds != prevSeconds) {
      tft.fillRect(10, 30, 118, 20, ST77XX_BLACK);
      
      tft.setTextSize(2);
      tft.setCursor(10, 35);
      tft.printf("%02lu:%02lu:%02lu", hours, minutes, seconds);
      
      prevHours = hours;
      prevMinutes = minutes;
      prevSeconds = seconds;
    }
    lastDisplayUpdate = currentTime;
  }
  
  int rawX = analogRead(X);
  int rawY = analogRead(Y);

  int centreredX = rawX - 1917;
  int centreredY = rawY - 1923;

  int controllerX = map(centreredX, -1917, 2178, -100, 100);
  int controllerY = map(centreredY, -1923, 2172, -100, 100);

  if (abs(controllerX) < 9) centreredX = 0;
  if (abs(controllerY) < 9) centreredY = 0;

  int ibusX = map(controllerX, -100, 100, 1000, 2000);
  int ibusY = map(controllerY, -100, 100, 1000, 2000);

  int dotX = gridCentreX + map(controllerY, -100, 100, -gridSize, gridSize);
  int dotY = gridCentreY - map(controllerX, -100, 100, -gridSize, gridSize);

  if (dotX != lastDotX || dotY != lastDotY) {
    tft.fillCircle(lastDotX, lastDotY, 3, ST77XX_BLACK);
    
    if (abs(lastDotY - gridCentreY) <= 3) {
      tft.drawLine(gridCentreX - gridSize, gridCentreY, gridCentreX + gridSize, gridCentreY, ST77XX_WHITE);
    }
    if (abs(lastDotX - gridCentreX) <= 3) {
      tft.drawLine(gridCentreX, gridCentreY - gridSize, gridCentreX, gridCentreY + gridSize, ST77XX_WHITE);
    }
    
    int distanceFromCentre= sqrt((lastDotX - gridCentreX) * (lastDotX - gridCentreX) + 
                                (lastDotY - gridCentreY) * (lastDotY - gridCentreY));
    if (distanceFromCentre >= gridSize - 4) {
      tft.drawCircle(gridCentreX, gridCentreY, gridSize, ST77XX_WHITE);
    }
    
    tft.fillCircle(dotX, dotY, 3, ST77XX_RED);
    
    lastDotX = dotX;
    lastDotY = dotY;
  }

  int z = digitalRead(Z);

  //Serial.printf("%d,%d,%d\n", ibusX, ibusY, !z);
  
  ibus.begin();
  
  ibus.write(ibusY);
  ibus.write(ibusX);
  ibus.write(z == LOW ? 2000 : 1000);

  ibus.end();

  delay(100);

}
