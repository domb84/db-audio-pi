# !/usr/local/bin/python
# Reading an analogue sensor with
# a single GPIO pin
# Author : Matt Hawkins
# Distribution : Raspbian
# Python : 2.7
# GPIO : RPi.GPIO v3.1.0a

import RPi.GPIO as GPIO, time, timeit

# Tell the GPIO library to use
# Broadcom GPIO references

# The wiring for the Teac T-H300DABmkII buttons / rotary is as follows:
# 1 : GND (BLACK WIRE)
# 2 : GPIO 19 (ROTARY DOWN)
# 3 : GPIO 26 (ROTARY UP)
# 4 : 3.V (POWER LED)
# 5 : GPIO 20 (POWER, DIMMER, MEM, AUTO TUN, ENTER, FUNC, INFO, BAND)
# 6 : GPIO 21 (TIMER, TIME ADJ, DAILY)
# 7 : NOT USED
# 8 : NOT USED


gpio = 20

GPIO.setmode(GPIO.BCM)

# Define function to measure charge time
def RCtime (PiPin):
    GPIO.setup(PiPin, GPIO.OUT)
    GPIO.output(PiPin, GPIO.HIGH) # Charge capacitor
    time.sleep(0.1)
    measurement = 0
    GPIO.setup(PiPin, GPIO.IN)
    # Count loops until voltage across
    # capacitor reads low on GPIO
    while GPIO.input(PiPin) == GPIO.LOW:
        measurement += 1
        # measurement = time.time()
    return measurement
# Main program loop
while True: print(RCtime(gpio)) # Measure timing using GPIO4