from time import sleep
from shairportmetadatareader import AirplayPipeListener

def on_track_info(lis, info):
    """
    Print the current track information.
    :param lis: listener instance
    :param info: track information
    """
    print(info)

listener = AirplayPipeListener() # You can use AirplayPipeListener or AirplayMQTTListener
listener.bind(track_info=on_track_info) # receive callbacks for metadata changes
listener.start_listening() # read the data asynchronously from the udp server
sleep(60) # receive data for 60 seconds
listener.stop_listening()
