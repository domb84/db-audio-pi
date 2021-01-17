from subprocess import call
from time import sleep

import includes.helpers as helpers
from blinker import signal
from rpilcdmenu import *
from rpilcdmenu.items import *

tools = helpers.tools()

class menu_manager:

    def __init__(self, service_list, device_name):
        self.set_mode = signal('set-mode')
        self.menu_accessed = signal('accessed')
        self.service_list = service_list
        self.device_name = device_name
        # init menu
        self.menu = RpiLCDMenu(7, 8, [25, 24, 23, 15], scrolling_menu=True)
        self.menu.items = []
        self.menu.message(('initialising...').upper(), autoscroll=True)

    def display_message(self, message, clear=False, static=False, autoscroll=False):
        # clear will clear the display and not render anything after (ie for shut down)
        # static will leave the message on screen
        # autoscroll will scroll the message then leave on screen
        # the default will show the message, then render the menu after 2 secondss

        if self.menu != None:
            # self.menu.clearDisplay()
            if clear == True:
                self.menu.message(message.upper())
                sleep(2)
                return self.menu.clearDisplay()
            elif static == True:
                return self.menu.message(message.upper(), autoscroll=False)
            elif autoscroll == True:
                return self.menu.message(message.upper(), autoscroll=True)
            else:
                self.menu.message(message.upper())
                sleep(2)
                return self.menu.render()
        return self

    def build_service_menu(self):

        # clear the menu
        if self.menu != None:
            self.menu.items = []

        try:
            # create submenu
            powermenu = RpiLCDSubMenu(self.menu)
            # create submenu button on main menu
            powermenu_button = SubmenuItem(('Power').upper(), powermenu, self.menu)
            # add to main menu
            self.menu.append_item(powermenu_button)
            powermenu.append_item(FunctionItem(('Back').upper(), self.exitSubMenu, [powermenu]))

            # create submenu of submenu
            rebootmenu = RpiLCDSubMenu(powermenu)
            # create submenu button on submenu
            rebootmenu_button = SubmenuItem(('Reboot').upper(), rebootmenu, powermenu)
            # add to submenu menu
            powermenu.append_item(rebootmenu_button)
            # add options to submenu
            rebootmenu.append_item(FunctionItem(('Back').upper(), self.exitSubMenu, [rebootmenu]))
            rebootmenu.append_item(FunctionItem(('Reboot Now').upper(), self.power, ['reboot']))

            # create submenu of submenu
            shutdownmenu = RpiLCDSubMenu(powermenu)
            # create submenu button on submenu
            shutdownmenu_button = SubmenuItem(('Shutdown').upper(), shutdownmenu, powermenu)
            # add to submenu menu
            powermenu.append_item(shutdownmenu_button)
            # add options to submenu
            shutdownmenu.append_item(FunctionItem(('Back').upper(), self.exitSubMenu, [shutdownmenu]))
            shutdownmenu.append_item(FunctionItem(('Shutdown Now').upper(), self.power, ['shutdown']))

            # create config submenu
            configmenu = RpiLCDSubMenu(self.menu)
            # create submenu button on main menu
            configmenu_button = SubmenuItem(('Configuration').upper(), configmenu, self.menu)
            # add to main menu
            self.menu.append_item(configmenu_button)
            # back button
            configmenu.append_item(FunctionItem(('Back').upper(), self.exitSubMenu, [configmenu]))

            # create mode submenu of config submenu
            modemenu = RpiLCDSubMenu(configmenu)
            # create submenu button on submenu
            modemenu_button = SubmenuItem(('Mode').upper(), modemenu, configmenu)
            # add to submenu menu
            configmenu.append_item(modemenu_button)
            # add options to submenu
            modemenu.append_item(FunctionItem(('Back').upper(), self.exitSubMenu, [modemenu]))
            # build current mode options
            for i in self.service_list:
                for k, v in i.items():
                    name = v['name']
                    service = v['details']['service']
                    if tools.service(service, 'status'):
                        # FunctionItem(Menu Entry, function, [function args])
                        service_option = FunctionItem(('%s<ON' % name).upper(), self.service_manager,
                                                      ['stop', name])
                        modemenu.append_item(service_option)
                    else:
                        service_option = FunctionItem(('%s' % name).upper(), self.service_manager,
                                                      ['start', name])
                        modemenu.append_item(service_option)

            # create wifi submenu of config submenu
            wifimenu = RpiLCDSubMenu(configmenu)
            # create submenu button on submenu
            wifimenu_button = SubmenuItem(('Wifi').upper(), wifimenu, configmenu)
            # add to submenu menu
            configmenu.append_item(wifimenu_button)
            # add options to submenu
            wifimenu.append_item(FunctionItem(('Back').upper(), self.exitSubMenu, [wifimenu]))

            if tools.app_status('nymea-networkmanager'):
                wifioption = FunctionItem(('Cancel setup').upper(), self.wifi_configuration, ['stop'])
                wifimenu.append_item(wifioption)
            else:
                wifioption = FunctionItem(('Setup Wifi').upper(), self.wifi_configuration, ['start'])
                wifimenu.append_item(wifioption)


        except Exception as e:
            print(e)

        # catch if the submenu sets the index too high, else menu will fail as it cannot select an item
        if self.menu.current_option > (len(self.menu.items) - 1):
            self.menu.current_option = (len(self.menu.items) - 1)

        # return rendered menu
        # if you do not return the menu it will render the original one again
        return self.menu.render()

    def service_manager(self, action, name):

        # set  variables
        failed = []
        service = None

        # get the service name you wish to action
        for i in self.service_list:
            for k, v in i.items():
                n = v['name']
                s = v['details']['service']
                d = v['details']['dependancies']
                if n == name:
                    service = s

        # stop all other services if you're starting another, then start the dependencies we need
        # or just stop them all if we're not supplied a named service to start
        if action == 'start' and service != None or action == 'stop-all' and name == None:
            # read all service items except the one you're starting and stop them and their dependencies
            # or stop all services
            for i in self.service_list:
                for k, v in i.items():
                    n2 = v['name']
                    s2 = v['details']['service']
                    d2 = v['details']['dependancies']
                    if n2 == name:
                        pass
                    else:
                        status = tools.service(s2, 'stop')
                        if status is False:
                            failed.append(n2)
                        for i in d2:
                            # print(i)
                            d_service = d2[i]['service']
                            d_on_action = d2[i]['on_action']
                            d_action = d2[i]['action']
                            if d_on_action == 'stop':
                                d_status = tools.service(d_service, d_action)
                                if d_status is False:
                                    # if d_action != 'disable':
                                    failed.append(d_service)
            # start the service dependenices
            for i in self.service_list:
                for k, v in i.items():
                    n3 = v['name']
                    s3 = v['details']['service']
                    d3 = v['details']['dependancies']
                    if n3 == name:
                        for i in d3:
                            # print(i)
                            d_service = d3[i]['service']
                            d_on_action = d3[i]['on_action']
                            d_action = d3[i]['action']
                            if d_on_action == 'start':
                                d_status = tools.service(d_service, d_action)
                                if d_status is False:
                                    # if d_action != 'disable':
                                    failed.append(d_service)

        # show error message on failure
        print("Had %s failures" % failed)
        if len(failed) > 0:
            for i in failed:
                self.display_message('Failed to stop or start\n%s' % i, autoscroll=True)

        elif service != None:
            # proceed with other action if theres no failures
            status = tools.service(service, action)
            print('Status of service is: %s ' % str(status))

            # if starting the service is successful
            if status is True and action == 'start':
                self.set_mode.send('menu_manager', mode=name)
                self.display_message('%s\nenabled' % name)
            # if stopping the service is successful
            elif status is True and action == 'stop':
                self.set_mode.send('menu_manager', mode=None)
                self.display_message('%s\ndisabled' % name)
            # if another option is successful
            elif status is True:
                self.display_message('%s\nprocessed' % name)
            # if starting the service is successful
            else:
                self.display_message('Failed to process\n%s ' % name)

        # print('Hit the end of service manager. Rebuilding menu.')
        return self.build_service_menu()


    def power(self, action):
        if action == 'shutdown':
            call(['sudo', 'shutdown', '-h', 'now'])
        if action == 'reboot':
            call(['sudo', 'shutdown', '-r', 'now'])
        return

    # exit sub menu
    def exitSubMenu(self, submenu):
        return submenu.exit()

    def dimmer(self):
        self.menu.lcd.displayToggle()

    def wifi_configuration(self, action):
        if action == 'start':
            result = tools.app_start('nymea-networkmanager',
                                     '-m always -a ' + self.device_name + ' -p ' + self.device_name)
            if result is True:
                self.display_message(('Open the berrylan application').upper())
            else:
                self.display_message(('Error starting wifi configuration').upper())
        elif action == 'stop':
            result = tools.app_kill('nymea-networkmanager')
            if result is True:
                self.display_message(('Configuration cancelled').upper())
            else:
                self.display_message(('Error cancelling configuration').upper(), )
        return self.build_service_menu()
