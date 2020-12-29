import ast
import configparser
import os
from subprocess import Popen, PIPE, call
import signal
import spotipy
import spotipy.oauth2
from spotipy.oauth2 import SpotifyOAuth
import sys
from shairportmetadatareader import AirplayUDPListener, AirplayPipeListener
from time import sleep

class helpers():

    def __init__(self):
        # self.kill = False
        self.config_path = "db_audio_pi.conf"
        self.config = self.configparser(self.config_path)
        try:
            self.SERVICES = ast.literal_eval(self.config['DEFAULT']['SERVICES'])
            self.DEVICE = self.config['DEFAULT']['DEVICE']
            self.SPOTIPY_CLIENT_ID = self.config['SPOTIFY']['ID']
            self.SPOTIPY_CLIENT_SECRET = self.config['SPOTIFY']['SECRET']
            self.SPOTIPY_REDIRECT_URI = self.config['SPOTIFY']['REDIRECT_URI']
            self.DEFAULT_SERVICE = self.config['DEFAULT']['DEFAULT_SERVICE']
        except:
            print("Variables not missing from conf")

    def configparser(self, path):
        self.config = configparser.ConfigParser()
        if os.path.exists(path):
            self.config.read(path)
            for i in self.config:
                print(i)
        return self.config

    def fooFunction(self, item_index):
        """
        sample method with a parameter
        """
        print("item %d pressed" % (item_index))

    # exit sub menu
    def exitSubMenu(self, submenu):
        return submenu.exit()

    def service(self, service, action):
        try:
            if action == "start":
                return_code = call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == "stop":
                return_code = call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == "enable":
                return_code = call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == "disable":
                return_code = call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == "status":
                return_code = call(['sudo', 'systemctl', 'is-active', '--quiet', service])
                return (return_code)
            elif action == "kill":
                check = Popen(['sudo', 'pgrep', '-c', service],stdout=PIPE)
                output, err = check.communicate()
                rc = check.returncode
                # strip 'b' and line breaks from output
                output = output.decode('utf-8').strip()
                # if both rc and the output don't equal 0 then theres a process. otherwise assume they're already dead and return 0
                if rc != "0" and output != "0":
                    return_code = call(['sudo', 'killall', '-q', service])
                    # print("return code is " +str(return_code))
                    return (return_code)
                else:
                    # print(output)
                    return (output)

        except Exception as e:
            print(e)
            return ("1")

    def power(self, action):
        if action == "shutdown":
            return_code = call(['sudo', 'shutdown', '-h', 'now'])


    def spotify(self, action):
        scope = "user-library-read user-read-playback-state"

        try:
            sp_oauth = SpotifyOAuth(open_browser=False, client_id=self.SPOTIPY_CLIENT_ID,
                                    client_secret=self.SPOTIPY_CLIENT_SECRET, redirect_uri=self.SPOTIPY_REDIRECT_URI,
                                    scope=scope, cache_path="cache")
            token_info = sp_oauth.get_cached_token()
            token = token_info['access_token']

            if not token_info:
                auth_url = sp_oauth.get_authorize_url()
                print(auth_url)
                response = input('Paste the above link into your browser, then paste the redirect url here: ')
                code = sp_oauth.parse_response_code(response)
                token_info = sp_oauth.get_access_token(code)
                token = token_info['access_token']

            sp = spotipy.Spotify(auth=token)

        except Exception as e:
            print("Cannot initialise Spotify information")

        def refresh():
            try:
                global token_info, sp
                if sp_oauth.is_token_expired(token_info):
                    token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                    token = token_info['access_token']
                    sp = spotipy.Spotify(auth=token)
            except Exception as e:
                print("Refreshing token failed")

        def current_playing_spotify():
            try:
                result = sp.current_user_playing_track()
                print(result)
                try:
                    artist = result['item']['artists'][0]['name']
                    track_name = result['item']['name']
                    return [artist, track_name]
                except:
                    print(result)
            except Exception as e:
                print(e)
                return None

        if action == "current":
            return current_playing_spotify()

    def bt_speaker(self, action):
        def current_playing_bt():
            track_info_path = "/tmp/.track"
            track_info = self.configparser(track_info_path)
            print(track_info)
            try:
                artist = track_info['INFO']['ARTIST']
                track_name = track_info['INFO']['TITLE']
                return [artist, track_name]
            except Exception as e:
                print(e)
                return None

        if action == "current":
            return current_playing_bt()

    def airplay(self, action):
        def current_playing_airplay(lis, info):
            """
            Print the current track information.
            :param lis: listener instance
            :param info: track information
            """
            print(info)

        # listener = AirplayUDPListener()  # You can use AirplayPipeListener or AirplayMQTTListener
        listener = AirplayPipeListener()
        listener.bind(track_info=current_playing_airplay)  # receive callbacks for metadata changes
        listener.start_listening()  # read the data asynchronously from the udp server
        sleep(60)  # receive data for 60 seconds
        listener.stop_listening()

        if action == "current":
            return current_playing_airplay()


    class app_shutdown:
        def _init_(self):
            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

        def exit_gracefully(self, signum, frame):
            self.shutdown_app()

        def shutdown_app(self):
            # global kill
            # kill = True
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)