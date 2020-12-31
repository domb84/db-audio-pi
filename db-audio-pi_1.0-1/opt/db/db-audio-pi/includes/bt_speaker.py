import configparser
import os
from time import sleep

from blinker import signal


class bt_speaker():

    def __init__(self, path):

        try:
            self.config = configparser.ConfigParser()
            self.path = path
            if os.path.exists(path):
                # init signal sender
                self.send_data = signal('send-data')
        except Exception as e:
            print(e)
            print("File path doesn't exist")

    def refresh(self):
        self.config.read(self.path)
        self.track_info = self.config

    def current_playing_bt(self):
        self.refresh()
        try:
            artist = self.track_info['INFO']['ARTIST']
            track_name = self.track_info['INFO']['TITLE']
            return {'status': 'playing', 'error': '', 'artist': artist, 'track': track_name}
        except Exception as e:
            return {'status': 'error', 'error': e, 'artist': '', 'track': ''}

    def listener(self):
        track_info = self.current_playing_bt()
        print(track_info)
        while True:
            new_track = self.current_playing_bt()
            if track_info != new_track:
                track_info = new_track
                # send data to signal
                self.send_data.send('bluetooth', status=track_info['status'], error=track_info['error'],
                                    artist=track_info['artist'], title=track_info['track'])
            sleep(1)
