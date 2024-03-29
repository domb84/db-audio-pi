import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

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
                logger.debug(i)
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
                logger.debug("Start service %s returned: %s" % (service, str(rc)))
                if rc == 0:
                    logger.debug("Started: %s" % service)
                    return True
                else:
                    logger.debug("Failed to start: %s" % service)
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
                logger.debug("Stop service %s returned: %s" % (service, str(rc)))
                if rc == 0 or 5:
                    logger.debug("Stopped: %s" % service)
                    return True
                else:
                    logger.debug("Failed to stop: %s" % service)
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
                logger.debug("Enable service %s returned: %s" % (service, str(rc)))
                if rc == 0:
                    logger.debug("Enabled: %s" % service)
                    return True
                else:
                    logger.debug("Failed to enable: $s" % service)
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
                logger.debug("Disable service %s returned: %s" % (service, str(rc)))
                if rc == 0:
                    logger.debug("Disabled: %s" % service)
                    return True
                else:
                    if 'does not exist' in output or err:
                        logger.debug("%s does not exist" % service)
                        return True
                    logger.debug("Failed to disable: %s" % service)
                    return False


            elif action == 'status':
                process = subprocess.Popen(['sudo', 'systemctl', 'is-active', '--quiet', service],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, err = process.communicate()
                rc = process.returncode
                logger.debug("Status of service %s returned: %s" % (service, str(rc)))
                if rc == 0:
                    logger.debug("Service %s running" % service)
                    return True
                else:
                    logger.debug("Service %s is not running" % service)
                    return False

        except Exception as e:
            logger.debug("Service processing failure: %s" % e)
            return False

    def app_status(self, application):
        # return True if running
        for proc in psutil.process_iter():
            try:
                # Check if process name contains the given name string.
                if application.lower() in proc.name().lower():
                    logger.debug("%s: running" % application)
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        logger.debug("%s: not running" % application)
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
        logger.debug("Kill %s return: %s" % (application, str(rc)))
        if rc == 0:
            logger.debug("Killed: %s" % application)
            return True
        else:
            logger.debug("Failed to kill: %s" % application)
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
            logger.debug("Started: %s with args: %s and rc: %s" % (application, arguments, str(rc)))
            return True
        else:
            logger.debug("Failed to start: %s with args: %s and rc: %s" % (application, arguments, str(rc)))
            return False

    def wifi(self):

        # return connected wifi status as dictionary  pairs
        process = subprocess.Popen(['sudo', 'iw', 'dev', 'wlan0', 'link'], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output, err = process.communicate(timeout=1)
        output = output.decode('utf-8').strip()
        err = err.decode('utf-8').strip()
        rc = process.returncode

        if rc == 0:
            if 'not connected' in output.lower():
                return 'Not connected'

            else:
                # cleanup mac address
                output = re.sub('(\w+):(\w+):(\w+):(\w+):(\w+):(\w+)', r':\1-\2-\3-\4-\5-\6', output)
                # remove tabs and split into list
                output = re.sub(r'\t', '', output).splitlines()
                # remove empty list items
                output = [x for x in output if x]
                # finally split into dictionary
                output = dict(x.split(':', 1) for x in output)
                # trim whitespace in all items
                output = {k.strip(): v.strip() for k, v in output.items()}
                # add signal %
                signal = int(re.sub(r' dBm', '', output['signal']))
                # calculate signal quality
                if (signal <= -100):
                    quality = 0
                elif (signal >= -50):
                    quality = 100
                else:
                    quality = 2 * (signal + 100)
                # add it to dictionary
                output['quality'] = quality

                return output
        else:
            return err


class app_shutdown:
    kill = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill = True
