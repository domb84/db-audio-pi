# from time import sleep
from shairportmetadatareader import AirplayPipeListener


class airplay():
    def on_track_info(lis, info):
        """
        Print the current track information.
        :param lis: listener instance
        :param info: track information
        """
        try:
            artist = info['songartist']
            track_name = info['itemname']
            print([artist, track_name])
        except:
            print(info)

    # listener = AirplayPipeListener()  # You can use AirplayPipeListener or AirplayMQTTListener
    listener = AirplayPipeListener()
    # listener.pipe_file('/tmp/shairport-sync-metadata')
    listener.bind(track_info=on_track_info)  # receive callbacks for metadata changes
    listener.start_listening()  # read the data asynchronously from the udp server
    # sleep(60)  # receive data for 60 seconds
    # listener.stop_listening()
