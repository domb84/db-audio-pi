import _thread
import ast
import threading
import time
from time import sleep

import adafruit_bitbangio as bitbangio
import adafruit_mcp3xxx.mcp3008 as MCP
import board
import digitalio
import includes.airplay as airplay
import includes.bt_speaker as bt_speaker
import includes.helpers as helpers
import includes.spotify as spotify
import pigpio
from RPi import GPIO
from adafruit_mcp3xxx.analog_in import AnalogIn
from rpilcdmenu import *
from rpilcdmenu.items import *

try:

    tools = helpers.tools()
    # init config
    config_path = 'db-audio-pi.conf'
    config = tools.configparser(config_path)
    try:
        services = ast.literal_eval(config['DEFAULT']['SERVICES'])
        DEVICE = config['DEFAULT']['DEVICE']
        SPOTIPY_CLIENT_ID = config['SPOTIFY']['ID']
        SPOTIPY_CLIENT_SECRET = config['SPOTIFY']['SECRET']
        SPOTIPY_REDIRECT_URI = config['SPOTIFY']['REDIRECT_URI']
        default_service = config['DEFAULT']['DEFAULT_SERVICE']
        BT_SPEAKER_TRACK_PATH = config['BT_SPEAKER']['TRACK_PATH']
    except:
        print("Variables missing from conf")
        exit(1)

    spotify = spotify.spotify(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)
    airplay = airplay.airplay
    bt_speaker = bt_speaker.bt_speaker(BT_SPEAKER_TRACK_PATH)

except Exception as e:
    print("Exiting with error : " + str(e))
    exit(1)

# set globals for encoder
last_A = 1
last_B = 1
last_gpio = 0

# set globals
menu = None
mode = None
menu_accessed = True
counter = 0
track_changed = True


# services = helpers.SERVICES
# default_service = helpers.DEFAULT_SERVICE


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
        elif 5000 <= chan1.value <= 9000:
            btn_press("Time Adj")
        elif 12000 <= chan1.value <= 15000:
            btn_press("Daily","Daily")
        elif 0 <= chan2.value <= 1000:
            btn_press("Power")
        elif 4000 <= chan2.value <= 9000:
            btn_press("Band")
        elif 11000 <= chan2.value <= 16000:
            btn_press("Function")
        elif 26000 <= chan2.value <= 28000:
            btn_press("Enter")
        elif 19000 <= chan2.value <= 22000:
            btn_press("Info")
        elif 39000 <= chan2.value <= 41000:
            btn_press("Auto Tuning")
        elif 32000 <= chan2.value <= 34000:
            btn_press("Memory")
        elif 44000 <= chan2.value <= 48000:
            btn_press("Dimmer")
        elif chan1.value <= 64000:
            print("Uncaught press on Channel 1 %s" % chan1.value)
        elif chan2.value <= 64000:
            print("Uncaught press on  Channel 2 %s" % chan2.value)
        time.sleep(0.1)


# button callback for mcp3008
def btn_press(btn):
    global menu, mode, menu_accessed
    # callback on button press
    if btn == "Enter":
        menu = menu.processEnter()
    if btn == "Auto Tuning":
        menu = menu.processEnter()
    if btn == "Info":
        playback_status(mode, "current")
    if btn == "Function":
        menu = menu.processUp()
    if btn == "Band":
        menu = menu.processDown()
    if btn == "Power":
        # kill main thread from spawned threads
        _thread.interrupt_main()
    menu_accessed = True
    time.sleep(0.25)
    return


# rotary encoder setup
def rotary_encoder():
    # setup rotary encoder variables for pigpio
    # BE SURE TO START PIGPIO IN PWM MODE "t -0"
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
    # backup function for encoder with standard GPIO. Does not work well at all.

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
            sleep(0.1)
    finally:
        GPIO.cleanup()


# rotary encoder callback
def rotary_turn(clockwise):
    global menu, menu_accessed
    if clockwise == True:
        menu = menu.processDown()
    if clockwise == False:
        menu = menu.processUp()
    menu_accessed = True
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
    if action == 'start' and service != None or action == 'stop-all' and name == None:
        # read all service items except the one you're starting and stop them and their dependencies
        # or stop all services
        for i in service_list:
            for k, v in i.items():
                n2 = v['name']
                s2 = v['details']['service']
                d2 = v['details']['dependancies']
                if n2 == name:
                    pass
                else:
                    status = str(tools.service(s2, 'stop'))
                    if status == "1":
                        failed.append(n2)
                    for i in d2:
                        # print(i)
                        d_service = d2[i]['service']
                        d_on_action = d2[i]['on_action']
                        d_action = d2[i]['action']
                        if d_on_action == 'stop':
                            d_status = str(tools.service(d_service, d_action))
                            if d_status == "1" and d_action != 'disable':
                                failed.append(d_service)
            # start the service dependenices
        for i in service_list:
            for k, v in i.items():
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
                            d_status = str(tools.service(d_service, d_action))
                            if d_status == "1" and d_action != 'disable':
                                failed.append(d_service)

    # show error message on failure
    if len(failed) > 0:
        for i in failed:
            display_message("Failed to stop or start %s service" % i)

    elif service != None:
        # proceed with other action if theres no failures
        status = str(tools.service(service, action))
        # if starting the service is successful
        if status == "0" and action == 'start':
            mode = name
            display_message("%s enabled" % name)
        elif status == "0" and action == 'stop':
            mode = None
            display_message("%s disabled" % name)
        elif status == "0":
            display_message("%s processed" % name)
        else:
            display_message("Failed to process %s " % name)

    if menu != None:
        return menu_create(service_list)
    return


def check_service(service):
    status = str(tools.service(service, 'status'))
    return status


def playback_status(mode, action, static=False):
    #  status modes
    #  current = current track
    if mode == None:
        if static:
            display_message("No mode set", static=True)
        else:
            display_message("No mode set", static=True)

    if mode == "spotify":
        result = spotify.current_playing_spotify()
        if result == None:
            if static:
                display_message("No track playing", static=True)
            else:
                display_message("No track playing")
        else:
            artist = result[0]
            track = result[1]
            if static:
                display_message(artist + "-" + track, static=True)
            else:
                display_message(artist + "-" + track)

    if mode == "bluetooth":
        try:
            result = bt_speaker.current_playing_bt()
        except Exception as e:
            print(e)

        if result == None:
            if static:
                display_message("No track playing", static=True)
            else:
                display_message("No track playing")
        else:
            artist = result[0]
            track = result[1]
            if static:
                display_message(artist + "-" + track, static=True)
            else:
                display_message(artist + "-" + track)

    if mode == "airplay":
        return


def display_message(message, clear=False, static=False):
    global menu

    if menu != None:
        menu.clearDisplay()
        menu.message(message.upper())
        time.sleep(2)
        if clear == True:
            return menu.clearDisplay()
        elif static == True:
            return
        else:
            return menu.render()
    return


def menu_create(services):
    # print ("Creating menu")
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
            for k, v in i.items():
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
    # menu.debug()
    return menu.render()


def main():
    global menu, default_service, services, mode, menu_accessed, counter, track_changed

    # mcp3008 on BaseThread with end callback
    mcp3008_thread = BaseThread(
        name='mcp3008',
        target=mcp3008_poll
        # callback=cb,
        # callback_args="fucksticks"
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

    # airplay thread
    airplay_thread = BaseThread(

        name='airplay',
        target=airplay
        # callback=rotary_turn,
        # callback_args=("direction")
    )

    airplay_thread.start()

    if menu == None:
        if default_service:
            service_manager(None, 'start', default_service, services)
        menu_create(services)

    currentmode = mode
    print(("Boot mode is %s" % currentmode))

    while True:
        # check for mode change
        if currentmode != mode:
            currentmode = mode
            print(("Mode has changed to %s" % currentmode))

        # check for menu access
        if menu_accessed == True:
            counter += 1
        elif track_changed == True and menu_accessed == False:
            playback_status(currentmode, 'current', static=True)

        # print(counter)
        if counter == 10:
            menu_accessed = False
            counter = 0

        if counter > 0:
            sleep(1)
        else:
            sleep(5)


if __name__ == "__main__":
    try:
        main()
    except:
        service_manager(None, 'stop-all', None, services)
        display_message("Bye!", clear=True)
        tools.app_shutdown().shutdown_app()
