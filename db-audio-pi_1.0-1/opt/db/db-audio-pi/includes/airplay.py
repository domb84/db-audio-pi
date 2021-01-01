# from time import sleep
from blinker import signal
from shairportmetadatareader import AirplayPipeListener


class airplay():
    def __init__(self):
        self.track_data = signal('track-data')

    def on_track_info(self, lis, info):
        """
        Print the current track information.
        :param lis: listener instance
        :param info: track information
        """
        try:
            songtime = info['songtime']
            try:
                # print(info)
                artist = info['songartist']
                track_name = info['itemname']
                self.track_data.send('airplay', status='playing', error='', artist=artist, title=track_name)
            except Exception as e:
                self.track_data.send('airplay', status='error', error=e, artist='', title='')
        except:
            # skip if 'songtime' is missing otherwise we send too many
            pass

    def listener(self):
        listener = AirplayPipeListener()
        listener.bind(track_info=self.on_track_info)  # receive callbacks for metadata changes
        listener.start_listening()  # read the data asynchronously from PIPE
