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
        self.track_id = None
        self.event = None
        self.artist = None
        self.title = None

        # TODO fix that if the .spot_track file doesnt exist it repeats ['INFO'] to the log


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
            logger.debug("Failed to get track meta.")
            return None

    def track_metadata(self, track_id):
        # Try and get track metadata, if it fails, refresh the token and try again, otherwise return None
        try:
            track = self.get_track_meta(track_id)
            # logger.debug(track)
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
        # read the spotify track info from the file and get meta
        try:
            updated = False
            self.config.read(self.path)
            track_info = self.config
            new_track_id = track_info['INFO']['ID']
            new_event = track_info['INFO']['EVENT']

            # check if the track has changed and get new metadata
            if new_track_id != self.track_id:

                logging.debug("Track ID changed from {0} to {1}, grabbing meta".format(self.track_id,new_track_id))

                self.track_id = new_track_id
                if self.track_id is not None:
                    track_metadata = self.track_metadata(self.track_id)
                    if track_metadata is not None:
                        self.artist = track_metadata[0]
                        self.title = track_metadata[1]
                        updated = True

            # check if the event has changed
            if new_event != self.event:
                # only update the event if it's not "change" as we have no use for changed tracks. The track ID would also have changed at that point.
                if new_event != "change":
                    self.event = new_event
                    updated = True

            if updated:
                return self.event, self.artist, self.title

        except Exception as e:
            logger.debug(e)
            return None



    def listener(self):
        # print the track status if it's changed in some way
        track_info = self.refresh()
        logger.debug(track_info)
        while True:
            new_track = self.refresh()
            if track_info != new_track:
                track_info = new_track
                # send data to signal
                if track_info is not None:
                    status = track_info[0]
                    artist = track_info[1]
                    track_name = track_info[2]
                    logger.debug(track_info)

                    self.track_data.send('spotify', status=status,
                                         artist=artist, title=track_name)
            sleep(1)
