#!/usr/bin/python

"""
menu with message view and physical steering
"""

from rpilcdmenu import *
from rpilcdmenu.items import *

import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from RPi import GPIO
import adafruit_bitbangio as bitbangio
import pigpio, time

# setup rotary encoder variables for pigpio
Enc_A = 17  # Encoder input A: input GPIO 17
Enc_B = 27  # Encoder input B: input GPIO 27
last_A = 1
last_B = 1
last_gpio = 0


def main():
    # create menu as in example3
    # global menu
    menu = RpiLCDMenu(7, 8, [25, 24, 23, 15])

    function_item1 = FunctionItem("Item 1", fooFunction, [1])
    function_item2 = FunctionItem("Item 2", fooFunction, [2])
    menu.append_item(function_item1).append_item(function_item2)

    # global submenu
    submenu = RpiLCDSubMenu(menu)
    submenu_item = SubmenuItem("SubMenu (3)", submenu, menu)
    menu.append_item(submenu_item)

    submenu.append_item(FunctionItem("Item 31", fooFunction, [31])).append_item(
        FunctionItem("Item 32", fooFunction, [32]))
    submenu.append_item(FunctionItem("Back", exitSubMenu, [submenu]))

    menu.append_item(FunctionItem("Item 4", fooFunction, [4]))

    menu.start()
    menu.debug()
    print("----")

    # press first menu item and scroll down to third one
    # menu.processEnter().processDown().processDown()
    # # enter submenu, press Item 32, press Back button
    # menu.processEnter().processDown().processEnter().processDown().processEnter()
    # # press item4 back in the menu
    # menu.processDown().processEnter()



    # mcp3008 button reader setup
    # create software spi
    spi = bitbangio.SPI(board.D11, MISO=board.D9, MOSI=board.D10)
    # create the cs (chip select)
    cs = digitalio.DigitalInOut(board.D22)
    # create the mcp object
    mcp = MCP.MCP3008(spi, cs)
    # create analog input channels on pins 6 and 7 of the mcp3008
    chan1 = AnalogIn(mcp, MCP.P6)
    chan2 = AnalogIn(mcp, MCP.P7)

    # setup rotary encoder in pigpio
    pi = pigpio.pi()  # init pigpio deamon
    pi.set_mode(Enc_A, pigpio.INPUT)
    pi.set_pull_up_down(Enc_A, pigpio.PUD_UP)
    pi.set_mode(Enc_B, pigpio.INPUT)
    pi.set_pull_up_down(Enc_B, pigpio.PUD_UP)
    pi.callback(lambda x: rotary_interrupt(Enc_A, pigpio.EITHER_EDGE, tim=None, item=menu))
    pi.callback(Enc_B, pigpio.EITHER_EDGE, rotary_interrupt)

    # main loop
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
        if 13000 <= chan2.value <= 14000:
            button_interrupt("Function")
        if 26000 <= chan2.value <= 27000:
            button_interrupt("Enter")
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

def exitSubMenu(item):
    return item.exit()

def Enter(item):
    return item.processEnter()

def scrollUp(item):
    return item.processDown()

def scrollDown(item):
    return item.processUp()

# Callback fn:
def rotary_interrupt(gpio, level, tim, item):
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
                scrollDown(item)
        elif gpio == Enc_B and level == 1:
            if last_A == 1:
                print("UP")
                scrollUp(item)


def button_interrupt(btn, item):
    print(btn + " has been pressed")
    if btn == "Enter":
        item.Enter()
    time.sleep(0.5)


if __name__ == "__main__":
    main()