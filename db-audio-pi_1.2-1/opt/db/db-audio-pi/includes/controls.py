from time import sleep

import adafruit_bitbangio as bitbangio
import adafruit_mcp3xxx.mcp3008 as MCP
import board
import digitalio
import pigpio
from adafruit_mcp3xxx.analog_in import AnalogIn
from blinker import signal


class controls:

    def __init__(self):
        self.controller = signal('controller')

    def rotary_encoder(self):
        # setup rotary encoder variables for pigpio
        # BE SURE TO START PIGPIO IN PWM MODE 't -0'
        Enc_A = 17  # Encoder input A: input GPIO 17
        Enc_B = 27  # Encoder input B: input GPIO 27

        # set globals for encoder
        self.last_A = 1
        self.last_B = 1
        self.last_gpio = 0

        def rotary_interrupt(gpio, level, tim):
            if gpio == Enc_A:
                self.last_A = level
            else:
                self.last_B = level

            if gpio != self.last_gpio:  # debounce
                self.last_gpio = gpio
                if gpio == Enc_A and level == 1:
                    if self.last_B == 1:
                        self.controller.send('controls', control='counter-clockwise')

                elif gpio == Enc_B and level == 1:
                    if self.last_A == 1:
                        self.controller.send('controls', control='clockwise')

        # setup rotary encoder in pigpio
        pi = pigpio.pi()  # init pigpio deamon
        pi.set_mode(Enc_A, pigpio.INPUT)
        pi.set_pull_up_down(Enc_A, pigpio.PUD_UP)
        pi.set_mode(Enc_B, pigpio.INPUT)
        pi.set_pull_up_down(Enc_B, pigpio.PUD_UP)
        pi.callback(Enc_A, pigpio.EITHER_EDGE, rotary_interrupt)
        pi.callback(Enc_B, pigpio.EITHER_EDGE, rotary_interrupt)

        print('Rotary thread start successfully, listening for turns')

    def buttons(self):
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

        print('MCP3008 thread start successfully, listening for buttons')

        while True:
            # read button states
            if 0 <= chan1.value <= 1000:
                self.controller.send('controls', control='timer')
            elif 5000 <= chan1.value <= 9000:
                self.controller.send('controls', control='time adj')
            elif 12000 <= chan1.value <= 15000:
                self.controller.send('controls', control='daily')
            elif 0 <= chan2.value <= 1000:
                self.controller.send('controls', control='power')
            elif 4000 <= chan2.value <= 9000:
                self.controller.send('controls', control='band')
            elif 11000 <= chan2.value <= 16000:
                self.controller.send('controls', control='function')
            elif 26000 <= chan2.value <= 29000:
                self.controller.send('controls', control='enter')
            elif 19000 <= chan2.value <= 22000:
                self.controller.send('controls', control='info')
            elif 39000 <= chan2.value <= 41000:
                self.controller.send('controls', control='auto tuning')
            elif 32000 <= chan2.value <= 34000:
                self.controller.send('controls', control='memory')
            elif 44000 <= chan2.value <= 48000:
                self.controller.send('controls', control='dimmer')
            elif chan1.value <= 64000:
                print('Uncaught press on Channel 1 %s' % chan1.value)
            elif chan2.value <= 64000:
                print('Uncaught press on  Channel 2 %s' % chan2.value)
            sleep(0.2)
