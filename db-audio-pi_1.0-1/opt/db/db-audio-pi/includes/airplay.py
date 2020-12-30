# from time import sleep
from blinker import signal
from shairportmetadatareader import AirplayPipeListener


class airplay():
    def __init__(self):
        self.current_track = signal('track')

    def on_track_info(self, lis, info):
        """
        Print the current track information.
        :param lis: listener instance
        :param info: track information
        """
        # print(info)
        try:
            artist = info['songartist']
            track_name = info['itemname']
            self.current_track.send([artist, track_name])
            # sleep(2)
        except:
            print(info)

    def listener(self):
        listener = AirplayPipeListener()
        listener.bind(track_info=self.on_track_info)  # receive callbacks for metadata changes
        listener.start_listening()  # read the data asynchronously from the udp server
