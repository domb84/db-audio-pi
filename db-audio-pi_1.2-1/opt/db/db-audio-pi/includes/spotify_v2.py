import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

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
            # import creds
            self.SPOTIPY_CLIENT_ID = client_id
            self.SPOTIPY_CLIENT_SECRET = client_secret
            self.access_token = None

            if os.path.exists(path):
                logger.debug('%s exists' % path)
            else:
                logger.debug('%s does not exist' % path)
        except Exception as e:
            logger.debug(e)

    def auth_token(self):
        # check if token is valid and refresh if necessary
        try:
            id = self.SPOTIPY_CLIENT_ID
            secret = self.SPOTIPY_CLIENT_SECRET
            if id is not "" and secret is not "":
                try:
                    # check if token is valid
                    BASE_URL = 'https://api.spotify.com/v1/'
                    params = {}
                    headers = {
                        'Authorization': 'Bearer {token}'.format(token=self.access_token)
                    }

                    r = requests.get(BASE_URL + 'me/', params=params, headers=headers)
                    r = r.json()

                    try:
                        status = r['error']['status']
                        message = r['error']['message']

                    except:
                        status = r['status']
                        message = r['message']

                    logger.debug("Token status and message: %s %s" % (status, message))

                    if status == 401 and 'invalid' in message.lower():
                        # refresh token
                        AUTH_URL = 'https://accounts.spotify.com/api/token'

                        # post
                        auth_response = requests.post(AUTH_URL, {
                            'grant_type': 'client_credentials',
                            'client_id': self.SPOTIPY_CLIENT_ID,
                            'client_secret': self.SPOTIPY_CLIENT_SECRET,
                        })

                        # convert the response to JSON
                        auth_response_data = auth_response.json()
                        logger.debug(auth_response_data)

                        # save the access token
                        self.access_token = auth_response_data['access_token']
                        
                        logger.debug("Token refreshed")

                    return True
                except Exception as e:
                    logger.debug(e)
                    return False

            else:
                logger.debug("No spotify ID or secret provided.")
                return False

        except Exception as e:
            logger.debug(e)
            return False

    def get_track_meta(self, track_id):
        try:
            BASE_URL = 'https://api.spotify.com/v1/'
            params = {'ids': track_id}
            headers = {
                'Authorization': 'Bearer {token}'.format(token=self.access_token)
            }

            r = requests.get(BASE_URL + 'tracks/', params=params, headers=headers)
            r = r.json()

            artists = []
            artist_list = r['tracks'][0]['artists']
            for artist in artist_list:
                artists.append(artist['name'])

            # join artists with comma
            artists = ", ".join(artists)

            track_name = r['tracks'][0]['name']
            return artists, track_name
        except:
            return None

    def track_metadata(self, track_id):
        try:
            track = self.get_track_meta(track_id)
            logger.debug(track)
            if track is not None:
                artists = track[0]
                track_name = track[1]
                return artists, track_name
            else:
                # refresh token and try again
                token = self.auth_token()
                track = self.get_track_meta(track_id)
                if track is not False:
                    artists = track[0]
                    track_name = track[1]
                    return artists, track_name
        except:
            return None

    def refresh(self):
        # read the spotify track info from the file
        try:
            self.config.read(self.path)
            self.track_info = self.config
            track_id = self.track_info['INFO']['ID']
            event = self.track_info['INFO']['EVENT']
            return event, track_id
        except:
            return None

    def listener(self):
        # Refreshes track file and sends to panel if its changed
        refresh = self.refresh()
        if refresh is not None:
            track_id = refresh[1]
            status = refresh[0]
        else:
            track_id = None
            status = None

        artist = None
        title = None

        while True:
            updated = False
            refresh = self.refresh()
            if refresh is not None:
                new_track_id = refresh[1]
                new_status = refresh[0]

                if new_status != status:
                    status = new_status
                    updated = True

                if new_track_id != track_id:
                    track_id = new_track_id
                    # send data to signal
                    if track_id is not None:
                        track_metadata = self.track_metadata(track_id)
                        if track_metadata is not None:
                            artist = track_metadata[0]
                            title = track_metadata[1]
                            updated = True

                if updated and artist is not None:
                    self.track_data.send('spotify', status=status,
                                         artist=artist, title=title)

                sleep(1)
