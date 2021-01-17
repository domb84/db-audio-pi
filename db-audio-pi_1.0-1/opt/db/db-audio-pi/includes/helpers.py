import configparser
import os
import signal
import subprocess

import psutil


class tools:

    def configparser(self, path):
        self.config = configparser.ConfigParser()
        if os.path.exists(path):
            self.config.read(path)
            for i in self.config:
                print(i)
        return self.config


    def service(self, service, action):
        try:
            if action == 'start':
                return_code = subprocess.call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == 'stop':
                return_code = subprocess.call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == 'enable':
                return_code = subprocess.call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == 'disable':
                return_code = subprocess.call(['sudo', 'systemctl', action, service, '--quiet'])
                return (return_code)
            elif action == 'status':
                return_code = subprocess.call(['sudo', 'systemctl', 'is-active', '--quiet', service])
                return (return_code)
            elif action == 'kill':
                check = subprocess.Popen(['sudo', 'pgrep', '-c', service], stdout=subprocess.PIPE)
                output, err = check.communicate()
                rc = check.returncode
                # strip 'b' and line breaks from output
                output = output.decode('utf-8').strip()
                # if both rc and the output don't equal 0 then theres a process. otherwise assume they're already dead and return 0
                if rc != '0' and output != '0':
                    return_code = subprocess.call(['sudo', 'killall', '-q', service])
                    # print('return code is ' +str(return_code))
                    return (return_code)
                else:
                    # print(output)
                    return (output)

        except Exception as e:
            print(e)
            return ('1')

    def app_status(self, application):
        # return True if running
        for proc in psutil.process_iter():
            try:
                # Check if process name contains the given name string.
                if application.lower() in proc.name().lower():
                    print("App is running")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        print("App not running")
        return False

    def app_kill(self, application):
        # Return True on success
        process = subprocess.Popen(['sudo', 'pkill', '-f', application], stdout=subprocess.PIPE)
        output, err = process.communicate()
        rc = process.returncode
        print("Stop return code from app_manager: %s" % str(rc))
        if rc == 0:
            print("App killed")
            return True
        else:
            print("App not killed")
            return False

    def app_start(self, application, arguments=None):
        # Return True if completed or long running process (None)
        app = ['sudo', application]
        if arguments != None:
            args = arguments.split()
            full_command = app + args
            command = subprocess.Popen(full_command, stdout=subprocess.PIPE)
        else:
            command = subprocess.Popen(app, stdout=subprocess.PIPE)
        rc = command.returncode
        print("Start return code from app_manager: %s" % str(rc))
        if rc != 1:
            return True
        else:
            return False

class app_shutdown:
    kill = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill = True
