import ast
import configparser
import os
import subprocess

import spotipy
import spotipy.oauth2
from spotipy.oauth2 import SpotifyOAuth

import json


class helpers():

    def __init__(self):
        self.kill = False
        self.config_path = "db_audio_pi.conf"
        self.config = self.configparser(self.config_path)
        try:
            self.services = ast.literal_eval(self.config['DEFAULT']['SERVICES'])
            self.DEVICE = self.config['DEFAULT']['DEVICE']
            self.SPOTIPY_CLIENT_ID = self.config['SPOTIFY']['ID']
            self.SPOTIPY_CLIENT_SECRET = self.config['SPOTIFY']['SECRET']
            self.SPOTIPY_REDIRECT_URI = self.config['SPOTIFY']['REDIRECT_URI']
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
                return_code = subprocess.call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == "stop":
                return_code = subprocess.call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == "status":
                return_code = subprocess.call(['sudo', 'systemctl', 'is-active', '--quiet', service])
                return (return_code)
        except:
            return ("1")

    def power(self, action):
        if action == "shutdown":
            return_code = subprocess.call(['sudo', 'shutdown', '-h', 'now'])


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

        def current_playing():
            try:
                result = sp.current_user_playing_track()
                artist = result['item']['artists'][0]['name']
                track_name = result['item']['name']
                return [artist, track_name]
            except Exception as e:
                print(e)
                return None

        if action == "current":
            return current_playing()
