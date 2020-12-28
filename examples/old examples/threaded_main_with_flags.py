import threading
import time
import logging
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import adafruit_bitbangio as bitbangio
import pigpio, time
from rpilcdmenu import *
from rpilcdmenu.items import *


logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s', )


def wait_for_event(e):
    logging.debug('wait_for_event starting')
    event_is_set = e.wait()
    logging.debug('event set: %s', event_is_set)


def wait_for_event_timeout(e, t):
    while not e.isSet():
        logging.debug('wait_for_event_timeout starting')
        event_is_set = e.wait(t)
        logging.debug('event set: %s', event_is_set)
        if event_is_set:
            logging.debug('processing event')
        else:
            logging.debug('doing other things')

# mcp3008 polling thread
def mcp3008_poll(e):
    # mcp3008 button reader setup
    # create software spi
    spi = bitbangio.SPI(board.D11, MISO=board.D9, MOSI=board.D10)
    # create the cs (chip select)
    cs = digitalio.DigitalInOut(board.D22)
    # create the mcp object
    mcp = MCP.MCP3008(spi, cs)
    # create analog input channels on pins 0 and 7 of the mcp3008
    chan1 = AnalogIn(mcp, MCP.P7)
    chan2 = AnalogIn(mcp, MCP.P0)

    print("MCP3008 thread start successfully, listening for buttons")

    while True:
        # read button states
        if 0 <= chan1.value <= 1000:
            btn_press("Timer")
        if 5900 <= chan1.value <= 7000:
            btn_press("Time Adj")
        if 12000 <= chan1.value <= 13000:
            btn_press("Daily")
        if 0 <= chan2.value <= 1000:
            btn_press("Power")
        if 5800 <= chan2.value <= 6100:
            btn_press("Band")
        if 13000 <= chan2.value <= 14000:
            btn_press("Function")
        if 26000 <= chan2.value <= 27000:
            btn_press("Enter")
        if 19000 <= chan2.value <= 21000:
            btn_press("Info")
        if 39000 <= chan2.value <= 41000:
            btn_press("Auto Tuning")
        if 33000 <= chan2.value <= 34000:
            btn_press("Memory")
        if 44000 <= chan2.value <= 46000:
            return e,"Dimmer"

# button callback for mcp3008
def btn_press(btn):
    # callback on button press
    print(threading.current_thread())
    print(btn + " pressed")
    time.sleep(0.25)



if __name__ == '__main__':
    e = threading.Event()
    t1 = threading.Thread(name='blocking',
                          target=wait_for_event,
                          args=(e,))
    t1.start()

    t2 = threading.Thread(name='non-blocking',
                          target=wait_for_event_timeout,
                          args=(e, 2))
    t2.start()

    t3 = threading.Thread(name='button',target=mcp3008_poll,args=(e,))
    t3.start()





    logging.debug('Waiting before calling Event.set()')
    time.sleep(3)
    # e.set()
    logging.debug('Event is set')
