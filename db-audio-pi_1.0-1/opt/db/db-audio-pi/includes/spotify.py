from time import sleep

import spotipy
import spotipy.oauth2
from blinker import signal
from spotipy.oauth2 import SpotifyOAuth


class spotify():

    def __init__(self, client_id, client_secret, redirect_uri):
        self.current_track = signal('track')

        self.SPOTIPY_CLIENT_ID = client_id
        self.SPOTIPY_CLIENT_SECRET = client_secret
        self.SPOTIPY_REDIRECT_URI = redirect_uri

        scope = "user-library-read user-read-playback-state"

        try:
            self.sp_oauth = SpotifyOAuth(open_browser=False, client_id=self.SPOTIPY_CLIENT_ID,
                                         client_secret=self.SPOTIPY_CLIENT_SECRET,
                                         redirect_uri=self.SPOTIPY_REDIRECT_URI,
                                         scope=scope)
            try:
                self.token_info = self.sp_oauth.get_cached_token()
                token = self.token_info['access_token']
            except:
                self.token_info = False

            if not self.token_info:
                auth_url = self.sp_oauth.get_authorize_url()
                print(auth_url)
                response = input('Paste the above link into your browser, then paste the redirect url here: ')
                code = self.sp_oauth.parse_response_code(response)
                self.token_info = self.sp_oauth.get_access_token(code)
                token = self.token_info['access_token']

            self.sp = spotipy.Spotify(auth=token)

        except Exception as e:
            print(e)
            print("Cannot initialise Spotify information")

    def refresh(self):
        try:
            if self.sp_oauth.is_token_expired(self.token_info):
                self.token_info = self.sp_oauth.refresh_access_token(self.token_info['refresh_token'])
                token = self.token_info['access_token']
                self.sp = spotipy.Spotify(auth=token)
            else:
                pass
        except Exception as e:
            print(e)
            print("Refreshing token failed")

    def current_playing_spotify(self):
        try:
            self.refresh()
            result = self.sp.current_user_playing_track()
            if result == None:
                return ['Spotify', 'Nothing playing']
            else:
                try:
                    artist = result['item']['artists'][0]['name']
                    track_name = result['item']['name']
                    return [artist, track_name]
                except Exception as e:
                    return ['Spotify', 'Information failed']
        except Exception as e:
            return ['Spotify', 'Information failed']

    def listener(self):
        track = self.current_playing_spotify()
        print(track)
        while True:
            new_track = self.current_playing_spotify()
            if track != new_track:
                track = new_track
                self.current_track.send(track)
                # print("Track changed")
            sleep(1)
