#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pigpiod version:

import pigpio, time

Enc_A = 17  # Encoder input A: input GPIO 17
Enc_B = 27  # Encoder input B: input GPIO 27

pi = 0

last_A = 1
last_B = 1
last_gpio = 0


def init():
    global pi

    pi = pigpio.pi()  # init pigpio deamon
    pi.set_mode(Enc_A, pigpio.INPUT)
    pi.set_pull_up_down(Enc_A, pigpio.PUD_UP)
    pi.set_mode(Enc_B, pigpio.INPUT)
    pi.set_pull_up_down(Enc_B, pigpio.PUD_UP)
    pi.callback(Enc_A, pigpio.EITHER_EDGE, rotary_interrupt)
    pi.callback(Enc_B, pigpio.EITHER_EDGE, rotary_interrupt)


# Callback fn:
def rotary_interrupt(gpio, level, tim):
    global last_A, last_B, last_gpio

    if gpio == Enc_A:
        last_A = level
    else:
        last_B = level

    if gpio != last_gpio:  # debounce
        last_gpio = gpio
        if gpio == Enc_A and level == 1:
            if last_B == 1:
                print("DOWN")
        elif gpio == Enc_B and level == 1:
            if last_A == 1:
                print("UP")


# init and loop forever (stop with CTRL C)
init()
while 1:
    time.sleep(1)