import ast
import os
import sys
import threading
import time
from time import sleep

from blinker import signal

import includes.airplay as airplay
import includes.bt_speaker as bt_speaker
import includes.controls as controls
import includes.helpers as helpers
import includes.menu_manager as menu_manager
import includes.spotify_v2 as spotify

# init signalling
track_data = signal('track-data')
controller = signal('controller')
set_mode = signal('set-mode')
menu_accessed = signal('accessed')

try:

    tools = helpers.tools()
    shutdown = helpers.app_shutdown()

    # init config
    config_path = 'db-audio-pi.conf'
    config = tools.configparser(config_path)
    services = ast.literal_eval(config['DEFAULT']['SERVICES'])
    DEVICE = config['DEFAULT']['DEVICE']
    SPOTIPY_CLIENT_ID = config['SPOTIFY']['ID']
    SPOTIPY_CLIENT_SECRET = config['SPOTIFY']['SECRET']
    # SPOTIPY_REDIRECT_URI = config['SPOTIFY']['REDIRECT_URI']
    SPOTIPY_TRACK_PATH = config['SPOTIFY']['TRACK_PATH']

    default_service = config['DEFAULT']['DEFAULT_SERVICE']
    BT_SPEAKER_TRACK_PATH = config['BT_SPEAKER']['TRACK_PATH']

    spotify = spotify.spotify(SPOTIPY_TRACK_PATH, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET).listener
    airplay = airplay.airplay().listener
    bt_speaker = bt_speaker.bt_speaker(BT_SPEAKER_TRACK_PATH).listener
    encoder = controls.controls().rotary_encoder
    buttons = controls.controls().buttons
    menu_manager = menu_manager.menu_manager(services, DEVICE)

except Exception as e:
    print('Exiting with error : ' + str(e))
    exit(1)


# set globals
mode = None
menu_accessed = True
counter = 0
last_song = {'artist': '', 'title': ''}


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


def shutdown_app():
    # print('Shutting down')
    try:
        menu_manager.display_message(('Shutting down \nsystem').upper(), clear=True)
        os._exit(0)
    except SystemExit:
        menu_manager.display_message(('Shutting down \nsystem').upper(), clear=True)
        sys.exit(0)


# subscribe to signal send data with receiver as the callback
@track_data.connect
def receiver(sender, **kw):
    global menu_accessed, mode, last_song
    # print('Got a signal sent by %r' % sender)
    # print('Message received from %s' % sender)

    if sender == 'request':
        if last_song['title'] != '':
            menu_manager.display_message(('%s\n%s' % (last_song['artist'], last_song['title'])), autoscroll=True)
        else:
            menu_manager.display_message('No track\ninformation'.upper())

    if sender == mode:
        status = kw['status']
        artist = kw['artist']
        title = kw['title']

        print(status)
        last_song = {'artist': artist, 'title': title}

        if menu_accessed == False:
            if status == 'playing':
                icon = '> '
            elif status == 'paused':
                icon = '||'
            else:
                icon = False

            if title != '':
                if icon:
                    menu_manager.display_message(('%s %s\n%s' % (icon, artist, title)), autoscroll=True)
                else:
                    menu_manager.display_message(('%s\n%s' % (artist, title)), autoscroll=True)

@set_mode.connect
def set_mode(sender, **kw):
    global mode
    mode = kw['mode']
    print('Mode changed to %s.' % mode)
    # do not attempt to  rebuild the menu here as it breaks the menu.
    # return menu_manager.build_service_menu(services)
    return

@controller.connect
def receive_controls(sender, **kw):
    global menu_accessed, mode

    print('Menu instance %s' % menu_manager)

    if kw['control'] == 'clockwise':
        menu_manager.menu = menu_manager.menu.processDown()
    if kw['control'] == 'counter-clockwise':
        menu_manager.menu = menu_manager.menu.processUp()
    if kw['control'] == 'enter':
        menu_manager.menu = menu_manager.menu.processEnter()
    if kw['control'] == 'auto tuning':
        menu_manager.menu = menu_manager.menu.processEnter()
    if kw['control'] == 'info':
        track_data.send('request')
    if kw['control'] == 'dimmer':
        menu_manager.dimmer()
    if kw['control'] == 'function':
        menu_manager.display_message(("current mode: \n%s" % mode).upper())
    if kw['control'] == 'band':
        pass
    if kw['control'] == 'timer':
        pass
    if kw['control'] == 'time adj':
        pass
    if kw['control'] == 'daily':
        pass
    if kw['control'] == 'auto tuning':
        pass
    if kw['control'] == 'memory':
        pass
    if kw['control'] == 'power':
        shutdown_app()
    menu_accessed = True
    time.sleep(0.25)
    return


def main():
    global default_service, services, menu_accessed, counter

    # build all the relevant threads
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
        # callback_args=('direction')
    )

    spotify_thread.start()

    if default_service:
        # start the default service
        menu_manager.service_manager('start', default_service)
    else:
        # only build the menu if no default service as it will get built but the mode signal
        menu_manager.build_service_menu()

    while not shutdown.kill:
        # check for menu access
        if menu_accessed == True:
            counter += 1

        # print(counter)
        if counter == 3:
            menu_accessed = False
            counter = 0
            # if last_song['title'] != '':
            #     menu_manager.display_message(('%s\n%s' % (last_song['artist'], last_song['title'])), autoscroll=True)
            # else:
            #     menu_manager.display_message('No track\ninformation'.upper())

        sleep(1)

    shutdown_app()


if __name__ == '__main__':
    try:
        main()
    except:
        shutdown_app()

