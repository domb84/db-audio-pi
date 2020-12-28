from nodemcu_gpio_lcd import GpioLcd
import RPi.GPIO as GPIO
from upymenu import Menu, MenuAction, MenuNoop

# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E = 8
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 15

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbers
GPIO.setup(LCD_E, GPIO.OUT)  # E
GPIO.setup(LCD_RS, GPIO.OUT)  # RS
GPIO.setup(LCD_D4, GPIO.OUT)  # DB4
GPIO.setup(LCD_D5, GPIO.OUT)  # DB5
GPIO.setup(LCD_D6, GPIO.OUT)  # DB6
GPIO.setup(LCD_D7, GPIO.OUT)  # DB7


def action_callback():
    print("callback action chosen")



submenu = Menu("Submenu")
submenu_action_1 = MenuAction("Submenu Action", callback=action_callback)
submenu_action_2 = MenuAction("Submenu Action 1", callback=action_callback)
submenu.add_option(submenu_action_1)
submenu.add_option(submenu_action_2)

menu_action = MenuAction("Action", callback=action_callback)
menu = Menu("Main Menu")
menu.add_option(submenu)
menu.add_option(menu_action)
menu.add_option(MenuNoop("Nothing here"))

lcd = GpioLcd(rs_pin=LCD_RS, enable_pin=LCD_E, d4_pin=LCD_D4, d5_pin=LCD_D5, d6_pin=LCD_D6, d7_pin=LCD_D7, num_lines=2, num_columns=20)

current_menu = menu.start(lcd) # Starts the menu on the LCD

menu.focus_next() # Focus on the next item in the menu
menu.focus_prev() # Focus on the previous item in the menu

# Choose the focused item, if it's and action execute
# the callback, or if it is a menu, render that menu.
menu = menu.choose()

# If it's a submenu, you can use the parent() function
# to navigate back up to the tree.
menu = menu.parent()
