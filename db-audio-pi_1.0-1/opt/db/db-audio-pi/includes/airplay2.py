from time import sleep

from blinker import signal


class airplay():
    def __init__(self):
        try:
            self.current_track = signal('track')
        except:
            print("Cannot init Airplay track info")

    def listener(self):
        track = ['Airplay', 'Track infomation disabled']
        while True:
            new_track = ['Airplay', 'Track infomation disabled']
            if track != new_track:
                track = new_track
                self.current_track.send(track)
            sleep(1)
