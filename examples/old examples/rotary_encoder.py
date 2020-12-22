# The wiring for the Teac T-H300DABmkII buttons / rotary is as follows:
# 1 : GND (BLACK WIRE)
# 2 : GPIO 19 (ROTARY DOWN)
# 3 : GPIO 26 (ROTARY UP)
# 4 : 3.V (POWER LED)
# 5 : MCP3008.P7 (POWER, DIMMER, MEM, AUTO TUN, ENTER, FUNC, INFO, BAND)
# 6 : MCP3008.P6 (TIMER, TIME ADJ, DAILY)
# 7 : NOT USED
# 8 : NOT USED

from RPi import GPIO
from time import sleep

clk = 19
dt = 26

GPIO.setmode(GPIO.BCM)
# set to GPIO.PUD_UP as the TEAC panel uses an encoder that is grounded
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

counter = 0
clkLastState = GPIO.input(clk)

try:

        while True:
                clkState = GPIO.input(clk)
                dtState = GPIO.input(dt)
                if clkState != clkLastState:
                        if dtState != clkState:
                                counter += 1
                        else:
                                counter -= 1
                        print(counter)
                clkLastState = clkState
                sleep(0.01)
finally:
        GPIO.cleanup()