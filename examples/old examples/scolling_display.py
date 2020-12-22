# radio.py, version 3.4 (RGB LCD Pi Plate version)
# September 14.3, 2013
# Edited by Dylan Leite
# Written by Sheldon Hartling for Usual Panic
# BSD license, all text above must be included in any redistribution
#

#
# based on code from Kyle Prier (http://wwww.youtube.com/meistervision)
# and AdaFruit Industries (https://www.adafruit.com)
# Kyle Prier - https://www.dropbox.com/s/w2y8xx7t6gkq8yz/radio.py
# AdaFruit   - https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code.git, Adafruit_CharLCDPlate
#

# dependancies
from Adafruit_I2C import Adafruit_I2C
from Adafruit_MCP230xx import Adafruit_MCP230XX
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from datetime import datetime
from subprocess import *
from time import sleep, strftime
from Queue import Queue
from threading import Thread

import smbus
import os
import time
import subprocess

# initialize the LCD plate
#   use busnum = 0 for raspi version 1 (256MB)
#   and busnum = 1 for raspi version 2 (512MB)
LCD = Adafruit_CharLCDPlate(busnum=1)
lcd = Adafruit_CharLCDPlate()

# Define a queue to communicate with worker thread
LCD_QUEUE = Queue()

# Globals
astring = ""
setscroll = ""

# Buttons
NONE = 0x00
SELECT = 0x01
RIGHT = 0x02
DOWN = 0x04
UP = 0x08
LEFT = 0x10
UP_AND_DOWN = 0x0C
LEFT_AND_RIGHT = 0x12


# ----------------------------
# WORKER THREAD
# ----------------------------

# Define a function to run in the worker thread
def update_lcd(q):
    while True:
        msg = q.get()
        # if we're falling behind, skip some LCD updates
        while not q.empty():
            q.task_done()
            msg = q.get()
        LCD.setCursor(0, 0)
        LCD.message(msg)
        q.task_done()
    return


# ----------------------------
# MAIN LOOP
# ----------------------------

def main():
    global astring, setscroll

    # Setup AdaFruit LCD Plate
    LCD.begin(16, 2)
    LCD.clear()
    LCD.backlight(LCD.ON)

    # Create the worker thread and make it a daemon
    worker = Thread(target=update_lcd, args=(LCD_QUEUE,))
    worker.setDaemon(True)
    worker.start()

    hostname = "12.10.191.251 "
    response = os.system("ping -c 1 " + hostname)
    if response == 0:
        internetradio = "load CBC"
        LCD.clear()
        LCD_QUEUE.put('Internet Found', True)
        sleep(2)
        radioSetup(internetradio)
    else:
        internetradio = "listall | mpc add"
        LCD.clear()
        LCD_QUEUE.put('Internet Lost', True)
        sleep(2)
        radioSetup(internetradio)


def radioSetup(internetradio):
    # ----------------------------
    # START THE MUSIC!
    # ----------------------------

    os.system("mpc clear")
    os.system("mpc %s" % internetradio)
    os.system("mpc play 1")
    countdown_to_play = 0
    sidescroll(setscroll, astring)

    # Main loop
    while True:
        press = read_buttons()

        # LEFT button pressed
        if (press == LEFT):
            volumestat = run_cmd("mpc volume 0")
            os.system("mpc prev")
            sleep(0.5)
            playstation = run_cmd("mpc | head -n 1")
            volumestat = run_cmd("mpc volume 100")
            sidescroll(setscroll, astring)

        # RIGHT button pressed
        if (press == RIGHT):
            volumestat = run_cmd("mpc volume 0")
            os.system("mpc next")
            sleep(0.5)
            playstation = run_cmd("mpc | head -n 1")
            volumestat = run_cmd("mpc volume 100")
            sidescroll(setscroll, astring)

        # UP button pressed
        if (press == UP):
            os.system("mpc volume +2")
            volumestat = run_cmd("mpc volume | head -n 1")
            LCD.clear()
            LCD_QUEUE.put(volumestat, True)
            sleep(0.5)
            sidescroll(setscroll, astring)

        # DOWN button pressed
        if (press == DOWN):
            os.system("mpc volume -2")
            volumestat = run_cmd("mpc volume | head -n 1")
            LCD.clear()
            LCD_QUEUE.put(volumestat, True)
            sleep(0.5)
            sidescroll(setscroll, astring)

        # SELECT button pressed
        if (press == SELECT):
            menu_pressed()

        # If we haven't had a key press in 300 msec
        # go ahead and issue the MPC command
        if (countdown_to_play > 0):
            countdown_to_play -= 1
            if (countdown_to_play == 0):
                # Play requested station
                os.system("mpc play")

        delay_milliseconds(99)
    update_lcd.join()


# ----------------------------
# READ SWITCHES
# ----------------------------

def read_buttons():
    buttons = LCD.buttons()
    # Debounce push buttons
    if (buttons != 0):
        while (LCD.buttons() != 0):
            delay_milliseconds(1)
    return buttons


def delay_milliseconds(milliseconds):
    seconds = milliseconds / float(1000)  # divide milliseconds by 1000 for seconds
    sleep(seconds)


# ----------------------------
# RADIO SETUP MENU
# ----------------------------

def menu_pressed():
    # global STATION

    MENU_LIST = [
        '1. Display Time\n&IP Address ',
        '2. System\nShutdown!    ',
        '3. System\nReboot!   ',
        '4. Restart\nScript    ',
        '5. Exit\n']

    item = 0
    LCD.clear()
    LCD.backlight(LCD.ON)
    LCD_QUEUE.put(MENU_LIST[item], True)

    keep_looping = True
    while (keep_looping):

        # Wait for a key press
        press = read_buttons()

        # UP button
        if (press == UP):
            item -= 1
            if (item < 0):
                item = len(MENU_LIST) - 1
            LCD.clear()
            LCD_QUEUE.put(MENU_LIST[item], True)

        # DOWN button
        elif (press == DOWN):
            item += 1
            if (item >= len(MENU_LIST)):
                item = 0
            LCD.clear()
            LCD_QUEUE.put(MENU_LIST[item], True)

        # SELECT button = exit
        elif (press == SELECT):
            keep_looping = False

            # Take action
            if (item == 0):
                # 1. display time and IP address
                display_ipaddr()
            elif (item == 1):
                # 2. shutdown the system
                LCD.clear()
                LCD_QUEUE.put('Shutting down\nLinux now! ...  ', True)
                LCD_QUEUE.join()
                output = run_cmd("mpc clear")
                output = run_cmd("sudo shutdown -hy 0")
                LCD.clear()
                LCD.backlight(LCD.OFF)
                exit(0)
            elif (item == 2):
                # 3. System Reboot
                LCD.clear()
                LCD_QUEUE.put('Rebooting\nLinux now! ...  ', True)
                LCD_QUEUE.join()
                output = run_cmd("sudo shutdown -ry 0")
                LCD.clear()
                LCD.backlight(LCD.OFF)
                exit(0)
            elif (item == 3):
                # 4 script restart
                main()
        else:
            delay_milliseconds(99)

    LCD.clear()
    LCD.backlight(LCD.ON)
    sidescroll(setscroll, astring)


# ----------------------------
# DISPLAY TIME AND IP ADDRESS
# ----------------------------

def display_ipaddr():
    show_eth0 = "ip addr show eth0  | cut -d/ -f1 | awk '/inet/ {printf \"e%15.15s\", $2}'"
    ipaddr = run_cmd(show_eth0)

    LCD.backlight(LCD.ON)
    i = 29
    muting = False
    keep_looping = True
    while (keep_looping):

        # Every 1/2 second, update the time display
        i += 1
        # if(i % 10 == 0):
        if (i % 5 == 0):
            LCD_QUEUE.put(datetime.now().strftime('%b %d  %H:%M:%S\n') + ipaddr, True)

        # Every 3 seconds, update ethernet or wi-fi IP address
        if (i == 60):
            ipaddr = run_cmd(show_eth0)
            i = 0

        # Every 100 milliseconds, read the switches
        press = read_buttons()
        # Take action on switch press

        # UP button pressed
        if (press == UP):
            output = run_cmd("mpc volume +2")

        # DOWN button pressed
        if (press == DOWN):
            output = run_cmd("mpc volume -2")

        # SELECT button = exit
        if (press == SELECT):
            keep_looping = False

        # LEFT or RIGHT toggles mute
        elif (press == LEFT or press == RIGHT):
            if muting:
                # amixer command not working, can't use next line
                # output = run_cmd("amixer -q cset numid=2 1")
                # mpc_play(STATION)
                # work around a problem.  Play always starts at full volume
                delay_milliseconds(400)
                output = run_cmd("mpc volume +2")
                output = run_cmd("mpc volume -2")
            else:
                # amixer command not working, can't use next line
                # output = run_cmd("amixer -q cset numid=2 0")
                output = run_cmd("mpc stop")
            muting = not muting

        delay_milliseconds(99)


# ----------------------------

def run_cmd(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    output = p.communicate()[0]
    return output


def sidescroll(setscroll, astring):
    LCD.clear()
    astring = run_cmd("mpc | head -n 1")
    volumestat = run_cmd("mpc volume | head -n 1")
    if " - " in astring:
        a, b, = astring.split(' - ')
        print
        "a =" + a
        print
        "b =" + b
    elif "streamtheworld" in astring:
        b, a, = astring.split('streamtheworld.com:3690/')
        print
        "b =" + b
        print
        "a =" + a
        a = " "
    setscroll = len(a)
    setscroll2 = len(b)
    LCD_QUEUE.put(a + "\n" + b, True)
    sleep(0.5)
    if setscroll >= 17:
        setscroll = setscroll - 17
        for i in range(setscroll):
            lcd.scrollDisplayLeft()
            sleep(0.4)
            LCD.clear()
            LCD_QUEUE.put(a + "\n" + b, True)
    elif setscroll2 >= 17:
        setscroll2 = setscroll2 - 17
        for i in range(setscroll2):
            lcd.scrollDisplayLeft()
            sleep(0.4)
            LCD.clear()
            LCD_QUEUE.put(a + "\n" + b, True)
    else:
        print
        "working"


if __name__ == '__main__':
    main()
