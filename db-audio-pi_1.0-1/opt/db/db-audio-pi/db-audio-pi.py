import ast
import os
import sys
import threading
import time
from time import sleep

import includes.airplay as airplay
import includes.bt_speaker as bt_speaker
import includes.controls as controls
import includes.helpers as helpers
import includes.spotify as spotify
from blinker import signal
from rpilcdmenu import *
from rpilcdmenu.items import *

# init signalling
send_data = signal('send-data')
controller = signal('controller')

try:

    tools = helpers.tools()
    shutdown = helpers.app_shutdown()


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

    spotify = spotify.spotify(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI).listener
    airplay = airplay.airplay().listener
    bt_speaker = bt_speaker.bt_speaker(BT_SPEAKER_TRACK_PATH).listener
    encoder = controls.controls().rotary_encoder
    buttons = controls.controls().buttons

except Exception as e:
    print("Exiting with error : " + str(e))
    exit(1)


# set globals
menu = None
mode = None
menu_accessed = True
counter = 0


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


def service_manager(item, action, name, service_list):
    global menu, mode

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


def display_message(message, clear=False, static=False):
    # clear will clear the display and not render anythng after
    # static will leave the message on screen
    # the default will render the menu after 2 seconds

    global menu

    if menu != None:
        menu.clearDisplay()
        if clear == True:
            menu.message(message.upper())
            time.sleep(2)
            menu.clearDisplay()
            return menu.clearDisplay()
        elif static == True:
            return menu.message(message.upper())
        else:
            menu.message(message.upper())
            time.sleep(2)
            return menu.render()

    return


def menu_create(services):
    # print ("Creating menu")
    global menu, mode

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


def shutdown_app():
    print("Shutting down")
    try:
        service_manager(None, 'stop-all', None, services)
        display_message("Bye!", clear=True)
        sys.exit(0)
    except SystemExit:
        service_manager(None, 'stop-all', None, services)
        display_message("Bye!", clear=True)
        os._exit(0)


# subscribe to signal send data with receiver as the callback
@send_data.connect
def receiver(sender, **kw):
    global menu_accessed, mode
    # print("Got a signal sent by %r" % sender)
    if menu_accessed == False:
        if sender == mode:
            # print("Message received from %s" % sender)
            status = kw['status']
            error = kw['error']
            artist = kw['artist']
            title = kw['title']
            print(artist, title)
            if status != '':
                display_message(("%s by %s" % (title, artist)), static=True)
            else:
                display_message(("%s: %s" % (status, error)), static=True)


@controller.connect
def receive_controls(sender, **kw):
    global menu, menu_accessed
    if kw['control'] == 'clockwise':
        menu = menu.processDown()
    if kw['control'] == 'counter-clockwise':
        menu = menu.processUp()
    if kw['control'] == "enter":
        menu = menu.processEnter()
    if kw['control'] == "auto tuning":
        menu = menu.processEnter()
    if kw['control'] == "info":
        pass
    if kw['control'] == "function":
        menu = menu.processUp()
    if kw['control'] == "band":
        menu = menu.processDown()
    if kw['control'] == "power":
        shutdown_app()
    menu_accessed = True
    time.sleep(0.25)

    menu_accessed = True
    return


def main():
    global menu, default_service, services, mode, menu_accessed, counter

    buttons_thread = BaseThread(
        name='buttons',
        target=buttons
    )

    buttons_thread.start()

    encoder_thread = BaseThread(
        name='encoder',
        target=encoder
    )

    encoder_thread.start()

    # bt thread
    bt_thread = BaseThread(

        name='bt',
        target=bt_speaker
    )

    bt_thread.start()

    # airplay thread
    airplay_thread = BaseThread(

        name='airplay',
        target=airplay
    )

    airplay_thread.start()

    # spotify thread
    spotify_thread = BaseThread(

        name='spotify',
        target=spotify
        # callback=rotary_turn,
        # callback_args=("direction")
    )

    spotify_thread.start()


    if menu == None:
        if default_service:
            service_manager(None, 'start', default_service, services)
        menu_create(services)

    currentmode = mode
    print(("Boot mode is %s" % currentmode))

    while not shutdown.kill:
        # check for mode change
        if currentmode != mode:
            currentmode = mode
            print(("Mode has changed to %s" % currentmode))

        # check for menu access
        if menu_accessed == True:
            counter += 1

        # print(counter)
        if counter == 3:
            menu_accessed = False
            counter = 0

        sleep(1)
    shutdown_app()

if __name__ == "__main__":
    try:
        main()
    except:
        shutdown_app()
