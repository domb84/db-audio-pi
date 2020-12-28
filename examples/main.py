#!/usr/bin/python

"""
multi level menu with physical steering
"""

from rpilcdmenu import *
from rpilcdmenu.items import *

import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import adafruit_bitbangio as bitbangio
import pigpio, time
from functools import partial

# setup rotary encoder variables for pigpio
Enc_A = 17  # Encoder input A: input GPIO 17
Enc_B = 27  # Encoder input B: input GPIO 27
last_A = 1
last_B = 1
last_gpio = 0
menu = RpiLCDMenu(7, 8, [25, 24, 23, 15])


def rotary_interrupt(gpio, level, tim):
    global last_A, last_B, last_gpio, menu

    if gpio == Enc_A:
        last_A = level
    else:
        last_B = level

    if gpio != last_gpio:  # debounce
        last_gpio = gpio
        if gpio == Enc_A and level == 1:
            if last_B == 1:
                print("DOWN")
                print(menu)
                menu = menu.processUp()
        elif gpio == Enc_B and level == 1:
            if last_A == 1:
                print("UP")
                print(menu)
                menu = menu.processDown()


def main():
    global menu

    # mcp3008 button reader setup
    # create software spi
    spi = bitbangio.SPI(board.D11, MISO=board.D9, MOSI=board.D10)
    # create the cs (chip select)
    cs = digitalio.DigitalInOut(board.D22)
    # create the mcp object
    mcp = MCP.MCP3008(spi, cs)
    # create analog input channels on pins 0 and 7 of the mcp3008
    chan1 = AnalogIn(mcp, MCP.P7)
    chan2 = AnalogIn(mcp, MCP.P0)

    # setup rotary encoder in pigpio
    g = partial(rotary_interrupt)
    pi = pigpio.pi()  # init pigpio deamon
    pi.set_mode(Enc_A, pigpio.INPUT)
    pi.set_pull_up_down(Enc_A, pigpio.PUD_UP)
    pi.set_mode(Enc_B, pigpio.INPUT)
    pi.set_pull_up_down(Enc_B, pigpio.PUD_UP)
    pi.callback(Enc_A, pigpio.EITHER_EDGE, rotary_interrupt)
    pi.callback(Enc_B, pigpio.EITHER_EDGE, rotary_interrupt)

    function_item1 = FunctionItem("Item 1", fooFunction, [1])
    function_item2 = FunctionItem("Item 2", fooFunction, [2])
    menu.append_item(function_item1).append_item(function_item2)

    submenu = RpiLCDSubMenu(menu)
    submenu_item = SubmenuItem("SubMenu (3)", submenu, menu)
    menu.append_item(submenu_item)

    submenu.append_item(FunctionItem("Item 31", fooFunction, [31])).append_item(
        FunctionItem("Item 32", fooFunction, [32]))
    submenu.append_item(FunctionItem("Back", exitSubMenu, [submenu]))

    menu.append_item(FunctionItem("Item 4", fooFunction, [4]))

    menu.start()

    while True:
        # read button states
        if 0 <= chan1.value <= 1000:
            button_interrupt("Timer")
        if 5900 <= chan1.value <= 7000:
            button_interrupt("Time Adj")
        if 12000 <= chan1.value <= 13000:
            button_interrupt("Daily")
        if 0 <= chan2.value <= 1000:
            button_interrupt("Power")
        if 5800 <= chan2.value <= 6100:
            button_interrupt("Band")
            menu = menu.processDown()
            print(menu)
        if 13000 <= chan2.value <= 14000:
            button_interrupt("Function")
            menu = menu.processUp()
            print(menu)
        if 26000 <= chan2.value <= 27000:
            button_interrupt("Enter")
            menu = menu.processEnter()
            print(menu)
        if 19000 <= chan2.value <= 21000:
            button_interrupt("Info")
        if 39000 <= chan2.value <= 41000:
            button_interrupt("Auto Tuning")
        if 33000 <= chan2.value <= 34000:
            button_interrupt("Memory")
        if 44000 <= chan2.value <= 46000:
            button_interrupt("Dimmer")


def fooFunction(item_index):
    """
    sample method with a parameter
    """
    print("item %d pressed" % (item_index))


def exitSubMenu(submenu):
    return submenu.exit()


def button_interrupt(btn):
    print(btn + " has been pressed")
    time.sleep(0.5)


if __name__ == "__main__":
    main()
