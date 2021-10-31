import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


from blinker import signal

import dbus, dbus.mainloop.glib, sys
from gi.repository import GLib



class bt_speaker():

    def __init__(self, path):

        # init signal sender
        self.track_data = signal('track-data')
        self.track_info = None
        self.event = None
        self.artist = None
        self.title = None


    def listener(self):
        def on_property_changed(interface, changed, invalidated):
            if interface != 'org.bluez.MediaPlayer1':
                return
            for prop, value in changed.items():

                # Set updated flag as none
                updated = None
                if prop == 'Status':
                    # set status
                    if value != self.event:
                        self.event = value
                        updated = True

                elif prop == 'Track':
                    for key in ('Title', 'Artist', 'Album'):
                        # set values
                        clean_value = value.get(key, '').strip()

                        if clean_value:
                            if key == 'Artist':
                                artist = clean_value
                            if key == 'Title':
                                title = clean_value
                            if key == 'Album':
                                album = clean_value

                    try:
                        if artist != self.artist or title != self.title:
                            self.artist = artist
                            self.title = title
                            updated = True
                    except:
                        logger.debug("Artist or title not set")

                    try:
                        # account for podcasts not having an artist and set the artist to the album name
                        if album != self.artist or title != self.title:
                            self.artist = album
                            self.title = title
                            updated = True
                    except:
                        logger.debug("Album or title not set")




            if updated:
                logger.debug("Sending status: {}, artist: {}, title: {}".format(self.event,self.artist,self.title))
                self.track_data.send('bluetooth', status=self.event,
                                 artist=self.artist, title=self.title)

        def on_playback_control(fd, condition):
            str = fd.readline()
            if str.startswith('play'):
                player_iface.Play()
            elif str.startswith('pause'):
                player_iface.Pause()
            elif str.startswith('next'):
                player_iface.Next()
            elif str.startswith('prev'):
                player_iface.Previous()
            elif str.startswith('vol'):
                vol = int(str.split()[1])
                if vol not in range(0, 128):
                    print('Possible Values: 0-127')
                    return True
                transport_prop_iface.Set(
                    'org.bluez.MediaTransport1',
                    'Volume',
                    dbus.UInt16(vol))
            return True

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        obj = bus.get_object('org.bluez', "/")
        mgr = dbus.Interface(obj, 'org.freedesktop.DBus.ObjectManager')
        player_iface = None
        transport_prop_iface = None
        for path, ifaces in mgr.GetManagedObjects().items():
            if 'org.bluez.MediaPlayer1' in ifaces:
                player_iface = dbus.Interface(
                    bus.get_object('org.bluez', path),
                    'org.bluez.MediaPlayer1')
            elif 'org.bluez.MediaTransport1' in ifaces:
                transport_prop_iface = dbus.Interface(
                    bus.get_object('org.bluez', path),
                    'org.freedesktop.DBus.Properties')
        if not player_iface:
            sys.exit('Error: Media Player not found.')
        if not transport_prop_iface:
            sys.exit('Error: DBus.Properties iface not found.')

        bus.add_signal_receiver(
            on_property_changed,
            bus_name='org.bluez',
            signal_name='PropertiesChanged',
            dbus_interface='org.freedesktop.DBus.Properties')
        GLib.io_add_watch(sys.stdin, GLib.IO_IN, on_playback_control)
        GLib.MainLoop().run()
