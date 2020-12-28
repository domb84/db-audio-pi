import threading

import adafruit_bitbangio as bitbangio
import adafruit_mcp3xxx.mcp3008 as MCP
import board
import digitalio
import pigpio
import time
from adafruit_mcp3xxx.analog_in import AnalogIn
from rpilcdmenu import *
from rpilcdmenu.items import *

import includes.helpers as helpers

try:
    helpers = helpers.helpers()
    services = helpers.services
except Exception as e:
    print("Exiting with error : " + str(e))

# set globals for encoder
last_A = 1
last_B = 1
last_gpio = 0

# init  menu
menu = None
mode = 'raspotify'


class BaseThread(threading.Thread):
    def __init__(self, callback=None, callback_args=None, *args, **kwargs):
        target = kwargs.pop('target')
        super(BaseThread, self).__init__(target=self.target_with_callback, *args, **kwargs)
        self.callback = callback
        self.method = target
        self.callback_args = callback_args

    def target_with_callback(self):
        self.method()
        if self.callback is not None:
            self.callback(*self.callback_args)


# mcp3008 polling thread
def mcp3008_poll():
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

    print("MCP3008 thread start successfully, listening for buttons")

    while True:
        # read button states
        if 0 <= chan1.value <= 1000:
            btn_press("Timer")
        if 5900 <= chan1.value <= 7000:
            btn_press("Time Adj")
        if 12000 <= chan1.value <= 13000:
            btn_press("Daily")
        if 0 <= chan2.value <= 1000:
            btn_press("Power")
        if 5800 <= chan2.value <= 6100:
            btn_press("Band")
        if 13000 <= chan2.value <= 14000:
            btn_press("Function")
        if 26000 <= chan2.value <= 27000:
            btn_press("Enter")
        if 19000 <= chan2.value <= 21000:
            btn_press("Info")
        if 39000 <= chan2.value <= 41000:
            btn_press("Auto Tuning")
        if 33000 <= chan2.value <= 34000:
            btn_press("Memory")
        if 44000 <= chan2.value <= 46000:
            btn_press("Dimmer")
        time.sleep(0.05)


# button callback for mcp3008
def btn_press(btn):
    global menu
    global mode
    # callback on button press
    if btn == "Enter":
        menu = menu.processEnter()
    if btn  == "Info":
        playback_status(mode, "current")
    time.sleep(0.25)


# rotary encoder setup
def rotary_encoder():
    # setup rotary encoder variables for pigpio
    Enc_A = 17  # Encoder input A: input GPIO 17
    Enc_B = 27  # Encoder input B: input GPIO 27

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
                    rotary_turn(clockwise=False)

            elif gpio == Enc_B and level == 1:
                if last_A == 1:
                    rotary_turn(clockwise=True)

    # setup rotary encoder in pigpio
    pi = pigpio.pi()  # init pigpio deamon
    pi.set_mode(Enc_A, pigpio.INPUT)
    pi.set_pull_up_down(Enc_A, pigpio.PUD_UP)
    pi.set_mode(Enc_B, pigpio.INPUT)
    pi.set_pull_up_down(Enc_B, pigpio.PUD_UP)
    pi.callback(Enc_A, pigpio.EITHER_EDGE, rotary_interrupt)
    pi.callback(Enc_B, pigpio.EITHER_EDGE, rotary_interrupt)

    print("Rotary thread start successfully, listening for turns")


# rotary encoder callback
def rotary_turn(clockwise):
    global menu
    if clockwise == True:
        menu = menu.processDown()
    if clockwise == False:
        menu = menu.processUp()


def service_enable_disable(item, action, service, name, disable, disable_name):
    global menu
    global mode

    # disable any conflicting services
    if disable != None and action == 'start':
        disabled = str(helpers.service(disable, 'stop'))
        # if it fails to disable the conflicting service, just exit
        if disabled == "1":
            menu.clearDisplay()
            menu.message("Failed to disable %s" % disable_name)
            time.sleep(2)
            menu = None
            menu_create(services)
            return menu.render()

    disabled = 0
    # start the service if it's successful
    status = str(helpers.service(service, action))
    menu.clearDisplay()

    # if starting the service is successful
    if status == "0" and action == 'start':
        mode = service
        menu.message("%s enabled" % name)

    # if disabling the service is successful
    elif status == "0" and action == 'stop':
        mode = None
        menu.message("%s disabled" % name)

    # if the service failed to start, start up the conflicting service again
    elif disabled != "1" and status != "0":
        disabled = str(helpers.service(disable, 'start'))
        if disabled != "0":
            menu.message("Failed to enable %s & %s" % name, disable_name)
        else:
            mode = disable

    else:
        menu.message("Failed to enable %s " % name)

    time.sleep(2)

    menu = None
    menu_create(services)
    return menu.render()


def check_service(service):
    status = str(helpers.service(service, 'status'))
    return status

def playback_status(mode, action):
    #  status modes
    #  current = current track

    global menu
    if mode == None:
        menu.clearDisplay()
        menu.message("No mode set")
        time.sleep(2)
        menu = None
        menu_create(services)
        return menu.render()

    if mode == "raspotify":
        result = helpers.spotify(action)
        if result == None:
            menu.clearDisplay()
            menu_create(services)
            return menu.render()
        menu.clearDisplay()
        artist = result[0]
        track = result[1]
        menu.message(artist + "-" + track)


def menu_create(service_list):
    global menu

    menu = RpiLCDMenu(7, 8, [25, 24, 23, 15])
    menu.clearDisplay()
    menu_item = 0

    try:
        for i in services:
            service = i['service']
            if check_service(service) == "0":
                menu_function = FunctionItem(i['name'] + " on", service_enable_disable,
                                             [menu_item, 'stop', i['service'], i['name'], i['disable'],
                                              i['disable_name']])
                menu.append_item(menu_function)
            else:
                menu_function = FunctionItem(i['name'] + " off", service_enable_disable,
                                             [menu_item, 'start', i['service'], i['name'], i['disable'],
                                              i['disable_name']])
                menu.append_item(menu_function)
    except Exception as e:
        print(e)

    return


def main():

    # move these threads out of here if theres a problem with controls
    # mcp3008 on BaseThread with callback
    mcp3008_thread = BaseThread(
        name='mcp3008',
        target=mcp3008_poll
        # callback=btn_press,
        # callback_args="Enter"
    )

    # start mcp3008 thread
    mcp3008_thread.start()

    rotary_encoder_thread = BaseThread(
        name='rotary_encoder',
        target=rotary_encoder
        # callback=rotary_turn,
        # callback_args=("direction")
    )

    # start rotary encoder thread
    rotary_encoder_thread.start()

    global menu

    # create intial menu
    menu_create(services)

    # start menu
    menu.start()
    menu.debug()

    input("Loaded")




if __name__ == "__main__":
    main()
