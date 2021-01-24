import configparser
import os
from time import sleep

from blinker import signal


class bt_speaker():

    def __init__(self, path):

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

    def refresh(self):
        try:
            self.config.read(self.path)
            self.track_info = self.config
            artist = self.track_info['INFO']['ARTIST']
            track_name = self.track_info['INFO']['TITLE']
            return artist, track_name
        except:
            return None

    def listener(self):
        track_info = self.refresh()
        # print(track_info)
        while True:
            new_track = self.refresh()
            if track_info != new_track:
                track_info = new_track
                # send data to signal
                if track_info is not None:
                    artist = track_info[0]
                    track_name = track_info[1]
                    self.track_data.send('bluetooth', status='playing',
                                         artist=artist, title=track_name)
            sleep(1)
