# The wiring for the Teac T-H300DABmkII buttons / rotary is as follows:
# 1 : GND (BLACK WIRE)
# 2 : GPIO 17 (ROTARY DOWN)
# 3 : GPIO 27 (ROTARY UP)
# 4 : 3.3V (POWER LED)
# 5 : MCP3008.P7 (POWER, DIMMER, MEM, AUTO TUN, ENTER, FUNC, INFO, BAND)
# 6 : MCP3008.P6 (TIMER, TIME ADJ, DAILY)
# 7 : NOT USED
# 8 : NOT USED

import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from RPi import GPIO
import adafruit_bitbangio as bitbangio
import pigpio, time

# setup rotary encoder variables for pigpio
Enc_A = 17  # Encoder input A: input GPIO 17
Enc_B = 27  # Encoder input B: input GPIO 27
last_A = 1
last_B = 1
last_gpio = 0


def main():

    # mcp3008 button reader setup
    # create software spi
    spi = bitbangio.SPI(board.D11, MISO=board.D9, MOSI=board.D10)
    # create the cs (chip select)
    cs = digitalio.DigitalInOut(board.D22)
    # create the mcp object
    mcp = MCP.MCP3008(spi, cs)
    # create analog input channels on pins 6 and 7 of the mcp3008
    chan1 = AnalogIn(mcp, MCP.P6)
    chan2 = AnalogIn(mcp, MCP.P7)

    # setup rotary encoder in pigpio
    pi = pigpio.pi()  # init pigpio deamon
    pi.set_mode(Enc_A, pigpio.INPUT)
    pi.set_pull_up_down(Enc_A, pigpio.PUD_UP)
    pi.set_mode(Enc_B, pigpio.INPUT)
    pi.set_pull_up_down(Enc_B, pigpio.PUD_UP)
    pi.callback(Enc_A, pigpio.EITHER_EDGE, rotary_interrupt)
    pi.callback(Enc_B, pigpio.EITHER_EDGE, rotary_interrupt)


    # main loop
    while True:
        # read button states
        if 0 <= chan1.value <= 1000:
            button_interrupt("Timer")
        if 5900 <= chan1.value <= 7000:
            button_interrupt("Time Adj")
        if 12000 <= chan1.value <= 13000:
            button_interrupt("Daily")
        if 0 <= chan2.value <= 1000:
            button_interrupt("Power")
        if 5800 <= chan2.value <= 6100:
            button_interrupt("Band")
        if 13000 <= chan2.value <= 14000:
            button_interrupt("Function")
        if 26000 <= chan2.value <= 27000:
            button_interrupt("Enter")
        if 19000 <= chan2.value <= 21000:
            button_interrupt("Info")
        if 39000 <= chan2.value <= 41000:
            button_interrupt("Auto Tuning")
        if 33000 <= chan2.value <= 34000:
            button_interrupt("Memory")
        if 44000 <= chan2.value <= 46000:
            button_interrupt("Dimmer")


# Callback fn:
def rotary_interrupt(gpio, level, tim):
    global last_A, last_B, last_gpio

    if gpio == Enc_A:
        last_A = level
    else:
        last_B = level

    if gpio != last_gpio:  # debounce
        last_gpio = gpio
        if gpio == Enc_A and level == 1:
            if last_B == 1:
                print("DOWN")
        elif gpio == Enc_B and level == 1:
            if last_A == 1:
                print("UP")


def button_interrupt(btn):
    print(btn + " has been pressed")
    time.sleep(0.5)


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print("Exiting controls")
        GPIO.cleanup()
