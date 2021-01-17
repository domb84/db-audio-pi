import configparser
import os
import re
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
                process = subprocess.Popen(['sudo', 'systemctl', action, service, '--quiet'], stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                output, err = process.communicate()
                try:
                    output = output.decode('utf-8').strip()
                    err = err.decode('utf-8').strip()
                except:
                    pass
                rc = process.returncode
                print("Start service %s returned: %s" % (service, str(rc)))
                if rc == 0:
                    print("Started: %s" % service)
                    return True
                else:
                    print("Failed to start: %s" % service)
                    return False

            elif action == 'stop':
                process = subprocess.Popen(['sudo', 'systemctl', action, service, '--quiet'], stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                output, err = process.communicate()
                try:
                    output = output.decode('utf-8').strip()
                    err = err.decode('utf-8').strip()
                except:
                    pass
                rc = process.returncode
                print("Stop service %s returned: %s" % (service, str(rc)))
                if rc == 0 or 5:
                    print("Stopped: %s" % service)
                    return True
                else:
                    print("Failed to stop: %s" % service)
                    return False

            elif action == 'enable':
                process = subprocess.Popen(['sudo', 'systemctl', action, service, '--quiet'], stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                output, err = process.communicate()
                try:
                    output = output.decode('utf-8').strip()
                    err = err.decode('utf-8').strip()
                except:
                    pass
                rc = process.returncode
                print("Enable service %s returned: %s" % (service, str(rc)))
                if rc == 0:
                    print("Enabled: %s" % service)
                    return True
                else:
                    print("Failed to enable: $s" % service)
                    return False

            elif action == 'disable':
                process = subprocess.Popen(['sudo', 'systemctl', action, service, '--quiet'], stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                output, err = process.communicate()
                try:
                    output = output.decode('utf-8').strip()
                    err = err.decode('utf-8').strip()
                except:
                    pass
                rc = process.returncode
                print("Disable service %s returned: %s" % (service, str(rc)))
                if rc == 0:
                    print("Disabled: %s" % service)
                    return True
                else:
                    if 'does not exist' in output or err:
                        print("%s does not exist" % service)
                        return True
                    print("Failed to disable: %s" % service)
                    return False


            elif action == 'status':
                process = subprocess.Popen(['sudo', 'systemctl', 'is-active', '--quiet', service],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, err = process.communicate()
                rc = process.returncode
                print("Status of service %s returned: %s" % (service, str(rc)))
                if rc == 0:
                    print("Service %s running" % service)
                    return True
                else:
                    print("Service %s is not running" % service)
                    return False

        except Exception as e:
            print("Service processing failure: %s" % e)
            return False

    def app_status(self, application):
        # return True if running
        for proc in psutil.process_iter():
            try:
                # Check if process name contains the given name string.
                if application.lower() in proc.name().lower():
                    print("%s: running" % application)
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        print("%s: not running" % application)
        return False

    def app_kill(self, application):
        # Return True on success
        process = subprocess.Popen(['sudo', 'pkill', '-f', application], stdout=subprocess.PIPE)
        output, err = process.communicate()
        try:
            output = output.decode('utf-8').strip()
            err = err.decode('utf-8').strip()
        except:
            pass
        rc = process.returncode
        print("Kill %s return: %s" % str(rc))
        if rc == 0:
            print("Killed: %s" % application)
            return True
        else:
            print("Failed to kill: %s" % application)
            return False

    def app_start(self, application, arguments=None):
        # Return True if completed or long running process (None)
        app = ['sudo', application]
        if arguments is not None:
            args = arguments.split()
            full_command = app + args
            command = subprocess.Popen(full_command, stdout=subprocess.PIPE)
        else:
            command = subprocess.Popen(app, stdout=subprocess.PIPE)
        rc = command.returncode
        if rc != 1:
            print("Started: %s with args: %s and rc: %s" % (application, arguments, str(rc)))
            return True
        else:
            print("Failed to start: %s with args: %s and rc: %s" % (application, arguments, str(rc)))
            return False

    def wifi(self):
        command = """jq --slurp --raw-input 'split("\n") | map(select(length > 0)|split(":") | {(.[0] ): (.[1:] | join(""))})'"""
        process = subprocess.Popen(['sudo', 'iw', 'dev', 'wlan0', 'link'], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output, err = process.communicate()
        try:
            output = output.decode('utf-8')
            # cleanup mac address
            output = re.sub("(\w+):(\w+):(\w+):(\w+):(\w+):(\w+)", r":\1-\2-\3-\4-\5-\6", output)
            # remove tabs and split into list
            output = re.sub(r'\t', '', output).splitlines()
            # remove empty list items
            output = [x for x in output if x]
            # finally split into dictionary
            d = dict(x.split(':', 1) for x in output)
            d = {k: v.strip() for k, v in d.items()}
            err = err.decode('utf-8').strip()
        except:
            pass
        rc = process.returncode
        print("Stop return code from app_manager: %s" % str(rc))
        if rc == 0:
            return d
        else:
            return err

class app_shutdown:
    kill = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill = True
