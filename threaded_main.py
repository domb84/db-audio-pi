import threading
import atexit
import adafruit_bitbangio as bitbangio
import adafruit_mcp3xxx.mcp3008 as MCP
import board
import digitalio
import pigpio
import time
from adafruit_mcp3xxx.analog_in import AnalogIn
from rpilcdmenu import *
from rpilcdmenu.items import *
from RPi import GPIO
from time import sleep

import includes.helpers as helpers

try:
    helpers = helpers.helpers()
    services = helpers.SERVICES
    default_service = helpers.DEFAULT_SERVICE
except Exception as e:
    print("Exiting with error : " + str(e))

# set globals for encoder
last_A = 1
last_B = 1
last_gpio = 0

# init  menu
menu = None
mode = 'raspotify'
count = 0

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
    if btn == "Auto Tuning":
        menu = menu.processEnter()
    if btn  == "Info":
        playback_status(mode, "current")
    if btn == "Function":
        menu = menu.processUp()
    if  btn == "Band":
        menu = menu.processDown()
    time.sleep(0.25)
    return



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

def rotary_encoder_2():
    clk = 17
    dt = 27

    GPIO.setmode(GPIO.BCM)
    # set to GPIO.PUD_UP as the TEAC panel uses an encoder that is grounded
    GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    counter = 0
    clkLastState = GPIO.input(clk)

    try:
        print("Rotary thread start successfully, listening for turns")
        while True:
            clkState = GPIO.input(clk)
            dtState = GPIO.input(dt)
            if clkState != clkLastState:
                sleep(0.1)
                if dtState != clkState:
                    rotary_turn(True)
                    counter += 1
                else:
                    rotary_turn(False)
                    counter -= 1
            clkLastState = clkState
    finally:
        GPIO.cleanup()

# rotary encoder callback
def rotary_turn(clockwise):
    global menu
    if clockwise == True:
        menu = menu.processDown()
    if clockwise == False:
        menu = menu.processUp()
    return



def service_manager(item, action, name, service_list):

    global menu
    global mode

    failed = []

    service = None
    # get the service name you wish to action
    for i in service_list:
        for k, v in i.items():
            n = v['name']
            s = v['details']['service']
            d = v['details']['dependancies']
            if n == name:
                service = s


    # print("service is " + str(service))
    # stop all other services if you're starting another, then start the dependencies we need
    if action == 'start' and service !=None or action == 'stop-all' and name == None:
        # read all service items except the one you're starting and stop them and their dependencies
        # or stop all services
        for i in service_list:
            for k,v in i.items():
                n2 = v['name']
                s2 = v['details']['service']
                d2 = v['details']['dependancies']
                if n2 == name:
                    pass
                else:
                    status = str(helpers.service(s2, 'stop'))
                    if status == "1":
                        failed.append(n2)
                    for i in d2:
                        # print(i)
                        d_service = d2[i]['service']
                        d_on_action = d2[i]['on_action']
                        d_action = d2[i]['action']
                        if d_on_action == 'stop':
                            d_status = str(helpers.service(d_service, d_action))
                            if d_status == "1" and d_action != 'disable':
                                failed.append(d_service)
            # start the service dependenices
        for i in service_list:
            for k,v in i.items():
                n3 = v['name']
                s3 = v['details']['service']
                d3 = v['details']['dependancies']
                if n3 == name:
                    for i in d3:
                        # print(i)
                        d_service = d3[i]['service']
                        d_on_action = d3[i]['on_action']
                        d_action = d3[i]['action']
                        if d_on_action == 'start':
                            d_status = str(helpers.service(d_service, d_action))
                            if d_status == "1" and d_action != 'disable':
                                failed.append(d_service)

    # show error message on failure
    if len(failed) > 0:
        display_message("Failed to stop or start %s services" % failed)

    elif service != None:
        # proceed with other action if theres no failures
        status = str(helpers.service(service, action))
        # if starting the service is successful
        if status == "0" and action == 'start':
            mode = service
            display_message("%s enabled" % name)
        elif status == "0" and action == 'stop':
            mode = None
            display_message("%s disabled" % name)
        elif status == "0":
            display_message("%s processed" % name)
        else:
            display_message("Failed to process %s " % name)

    if menu!=None:
        return menu_create(service_list)
    return

def check_service(service):
    status = str(helpers.service(service, 'status'))
    return status

def playback_status(mode, action):
    #  status modes
    #  current = current track
    if mode == None:
        display_message("No mode set")

    if mode == "raspotify":
        result = helpers.spotify(action)
        if result == None:
            display_message("No track playing")
        else:
            artist = result[0]
            track = result[1]
            display_message(artist + "-" + track)

    if mode == "bt_speaker":
        result = helpers.bt_speaker(action)
        if result == None:
            display_message("No track playing")
        else:
            artist = result[0]
            track = result[1]
            display_message(artist + "-" + track)

    if mode == "shairport-sync":
        result = helpers.airplay(action)
        if result == None:
            display_message("No track playing")
        else:
            artist = result[0]
            track = result[1]
            display_message(artist + "-" + track)



def display_message(message):
    global menu
    if menu!=None:
        menu.clearDisplay()
        menu.message(message.upper())
        time.sleep(2)
        print(menu)
        return menu.render()
    return

def menu_create(services):
    print ("Creating menu")
    global menu
    global mode

    if menu == None:
        # print("init menu")
        menu = RpiLCDMenu(7, 8, [25, 24, 23, 15])
        display_message("Initialising")
    if menu != None:
        # print("re-init menu")
        menu = RpiLCDMenu(7, 8, [25, 24, 23, 15])

    menu_item = 1

    try:
        for i in services:
            for k,v in i.items():
                name = v['name']
                service = v['details']['service']
                dependancies = v['details']['dependancies']
                if check_service(service) == "0":
                    menu_function = FunctionItem(("%s ON" % name).upper(), service_manager,
                                                 [menu_item, 'stop', name, services])
                    menu.append_item(menu_function)
                    menu_item = + 1
                else:
                    menu_function = FunctionItem(("%s OFF" % name).upper(), service_manager,
                                                 [menu_item, 'start', name, services])
                    menu.append_item(menu_function)
                    menu_item = + 1

    except Exception as e:
        print(e)
    menu.start()
    menu.debug()
    return menu.render()


def main():

    global menu, default_service, services

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
        target=rotary_encoder_2
        # callback=rotary_turn,
        # callback_args=("direction")
    )

    # start rotary encoder thread
    rotary_encoder_thread.start()


    if menu == None:
        if default_service:
            service_manager(0, 'start', default_service, services)
        menu_create(services)


    input("Loaded")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        service_manager(None, 'stop-all', None , services)
        display_message("Bye!")
        helpers.app_shutdown().shutdown_app()
