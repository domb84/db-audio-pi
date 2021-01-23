import configparser
import os
from time import sleep

import requests
from blinker import signal


# useful info
# https://github.com/librespot-org/librespot/issues/185
# https://stmorse.github.io/journal/spotify-api.html

class spotify():

    def __init__(self, path, client_id, client_secret):
        # init signal sender
        self.track_data = signal('track-data')

        try:
            self.config = configparser.ConfigParser()
            self.path = path
            if os.path.exists(path):
                print('%s exists' % path)
            else:
                print('%s does not exist' % path)
        except Exception as e:
            print(e)

        # import creds
        self.SPOTIPY_CLIENT_ID = client_id
        self.SPOTIPY_CLIENT_SECRET = client_secret
        self.access_token = None

    def auth_token(self):
        AUTH_URL = 'https://accounts.spotify.com/api/token'

        # POST
        auth_response = requests.post(AUTH_URL, {
            'grant_type': 'client_credentials',
            'client_id': self.SPOTIPY_CLIENT_ID,
            'client_secret': self.SPOTIPY_CLIENT_SECRET,
        })

        # convert the response to JSON
        auth_response_data = auth_response.json()

        # save the access token
        self.access_token = auth_response_data['access_token']
        return True

    def track_metadata(self, track_id):
        result = self.auth_token()
        print(track_id)

        if result is not False:

            BASE_URL = 'https://api.spotify.com/v1/'
            params = {'ids': track_id}
            headers = {
                'Authorization': 'Bearer {token}'.format(token=self.access_token)
            }

            r = requests.get(BASE_URL + 'tracks/', params=params, headers=headers)
            r = r.json()
            print(r)

            try:
                artist = r['tracks'][0]['artists'][0]['name']
                track_name = r['tracks'][0]['name']
                print(artist, track_name)
                return {'status': 'playing', 'error': '', 'artist': artist, 'track': track_name}
            except Exception as e:
                return {'status': 'error', 'error': e, 'artist': '', 'track': ''}

    def refresh(self):
        self.config.read(self.path)
        self.track_info = self.config

    def listener(self):
        self.refresh()
        # try:
        track_id = self.track_info['INFO']['ID']
        event = self.track_info['INFO']['EVENT']
        self.auth_token()
        track_metadata = self.track_metadata(track_id)
        print(track_metadata)

        while True:
            self.refresh()
            try:
                new_track_id = self.track_info['INFO']['ID']
            except:
                new_track_id = None

            if track_id != new_track_id:
                track_id = new_track_id

                # get track metadata
                track_metadata = self.track_metadata(track_id)

                # send data to signal
                self.track_data.send('spotify', status=track_metadata['status'], error=track_metadata['error'],
                                     artist=track_metadata['artist'], title=track_metadata['track'])
            sleep(1)
