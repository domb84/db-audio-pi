import configparser
import os
from time import sleep

from blinker import signal


class bt_speaker():

    def __init__(self, path):
        try:
            self.config = configparser.ConfigParser()
            if os.path.exists(path):
                self.path = path
            self.current_track = signal('track')
        except:
            print("File path doesn't exist")

    def refresh(self):
        self.config.read(self.path)
        self.track_info = self.config

    def current_playing_bt(self):
        self.refresh()
        try:
            artist = self.track_info['INFO']['ARTIST']
            track_name = self.track_info['INFO']['TITLE']
            # self.current_track.send([artist, track_name])
            return [artist, track_name]
        except Exception as e:
            print(e)
            return None

    def listener(self):
        track = self.current_playing_bt()
        while True:
            new_track = self.current_playing_bt()
            if track != new_track:
                track = new_track
                self.current_track.send(track)
            sleep(1)
