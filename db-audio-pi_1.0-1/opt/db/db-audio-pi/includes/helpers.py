import configparser
import os
import signal
import sys
from subprocess import Popen, PIPE, call
from time import sleep

from shairportmetadatareader import AirplayPipeListener

kill = False


class tools:

    def configparser(self, path):
        self.config = configparser.ConfigParser()
        if os.path.exists(path):
            self.config.read(path)
            for i in self.config:
                print(i)
        return self.config

    def fooFunction(self, item_index):

        """
        sample method with a parameter
        """
        print("item %d pressed" % (item_index))

    # exit sub menu
    def exitSubMenu(self, submenu):
        return submenu.exit()

    def service(self, service, action):
        try:
            if action == "start":
                return_code = call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == "stop":
                return_code = call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == "enable":
                return_code = call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == "disable":
                return_code = call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == "status":
                return_code = call(['sudo', 'systemctl', 'is-active', '--quiet', service])
                return (return_code)
            elif action == "kill":
                check = Popen(['sudo', 'pgrep', '-c', service], stdout=PIPE)
                output, err = check.communicate()
                rc = check.returncode
                # strip 'b' and line breaks from output
                output = output.decode('utf-8').strip()
                # if both rc and the output don't equal 0 then theres a process. otherwise assume they're already dead and return 0
                if rc != "0" and output != "0":
                    return_code = call(['sudo', 'killall', '-q', service])
                    # print("return code is " +str(return_code))
                    return (return_code)
                else:
                    # print(output)
                    return (output)

        except Exception as e:
            print(e)
            return ("1")

    def power(self, action):
        if action == "shutdown":
            return_code = call(['sudo', 'shutdown', '-h', 'now'])

    def bt_speaker(self, action):
        def current_playing_bt():
            track_info_path = "/tmp/.track"
            track_info = self.configparser(track_info_path)
            print(track_info)
            try:
                artist = track_info['INFO']['ARTIST']
                track_name = track_info['INFO']['TITLE']
                return [artist, track_name]
            except Exception as e:
                print(e)
                return None

        if action == "current":
            return current_playing_bt()

    def airplay(self):
        def on_track_info(lis, info):
            """
            Print the current track information.
            :param lis: listener instance
            :param info: track information
            """
            print(info)

        listener = AirplayPipeListener()  # You can use AirplayPipeListener or AirplayMQTTListener
        listener.bind(track_info=on_track_info)  # receive callbacks for metadata changes
        listener.start_listening()  # read the data asynchronously from the udp server
        sleep(60)  # receive data for 60 seconds
        listener.stop_listening()

    class app_shutdown:
        def _init_(self):
            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

        def exit_gracefully(self, signum, frame):
            self.shutdown_app()

        def shutdown_app(self):
            global kill
            kill = True
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
