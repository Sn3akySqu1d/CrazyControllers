import csv
import serial
import time

arduino_port = "COM13"
baud = 9600
fileName="Dataset.csv"

ser = serial.Serial(arduino_port, baud)
print("Connected to Arduino port:" + arduino_port)
file = open(fileName, "a")
print("Opened file")

samples = 1000
line = 0 
sensor_data = []

time.sleep(10)

while line <= samples:
    ser.flushInput()

    getData=ser.readline()
    dataString = getData.decode('utf-8')
    data = dataString[0:][:-2]

    readings = data.split(",")
    readings.append("Rest")
    if (len(readings) == 8 and readings[0] != ""):
        sensor_data.append(readings)
        print(line)
        line = line + 1

with open(fileName, 'a', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(sensor_data)

print("Data collection complete")
file.close()