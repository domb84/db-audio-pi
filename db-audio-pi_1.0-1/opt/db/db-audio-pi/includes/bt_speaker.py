import configparser
import os


class bt_speaker():

    def __init__(self, path):
        try:
            self.config = configparser.ConfigParser()
            if os.path.exists(path):
                self.path = path
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
            print(artist, track_name)
            return [artist, track_name]
        except Exception as e:
            print(e)
            return None
