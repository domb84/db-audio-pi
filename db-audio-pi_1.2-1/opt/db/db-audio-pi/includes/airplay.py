# from time import sleep
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

from blinker import signal
from shairportmetadatareader import AirplayPipeListener


class airplay():
    def __init__(self):
        self.track_data = signal('track-data')

    def on_track_info(self, lis, info):
        '''
        logger.debug the current track information.
        :param lis: listener instance
        :param info: track information
        '''
        # logger.debug(info)
        # logger.debug(lis)
        try:
            songtime = info['songtime']
            artist = info['songartist']
            track_name = info['itemname']
            self.track_data.send('airplay', status='playing', artist=artist, title=track_name)
        except:
            # skip if 'songtime' is missing otherwise we send too many
            pass
        return

    def listener(self):
        listener = AirplayPipeListener()
        listener.bind(track_info=self.on_track_info)  # receive callbacks for metadata changes
        listener.start_listening()  # read the data asynchronously from PIPE
