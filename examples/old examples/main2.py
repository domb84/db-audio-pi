#!/usr/bin/python


import pigpio, time
import examples.lcdmenu4 as lcdmenu

# setup rotary encoder variables for pigpio
Enc_A = 17  # Encoder input A: input GPIO 17
Enc_B = 27  # Encoder input B: input GPIO 27
last_A = 1
last_B = 1
last_gpio = 0
kill = False

def main():

    menu = lcdmenu.Menu()
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
                    menu.Up()
            elif gpio == Enc_B and level == 1:
                if last_A == 1:
                    print("UP")
                    menu.Down()

    def mcp3008_interrupt(gpio, level, tim):
        if level == 200:
            print ("Enter button pressed")
        time.sleep(0.5)


    pi = pigpio.pi()  # init pigpio deamon

    # setup rotary encoder in pigpio
    pi.set_mode(Enc_A, pigpio.INPUT)
    pi.set_pull_up_down(Enc_A, pigpio.PUD_UP)
    pi.set_mode(Enc_B, pigpio.INPUT)
    pi.set_pull_up_down(Enc_B, pigpio.PUD_UP)

    # setup mcp3008 for button reads on pigpio
    CS = 22
    MISO = 9
    MOSI = 10
    SCLK = 11
    MODE = 0


    pi.bb_spi_close(CS)  # because I use ctrl-C to break each time
    pi.bb_spi_open(CS, MISO, MOSI, SCLK, 10000, MODE)

    # setup callbacks
    pi.callback(Enc_A, pigpio.EITHER_EDGE, rotary_interrupt) # knob down
    pi.callback(Enc_B, pigpio.EITHER_EDGE, rotary_interrupt) # knob up


    # I DON"T UNDERSTAND HOW TO MAKE THIS WORK
    pi.callback(SCLK, pigpio.EITHER_EDGE, mcp3008_interrupt)

    while True:
        # pi.bb_spi_xfer(CS, [1, (8 + 0) << 4, 0])
        # for n in range(8):
        #     ct, data = pi.bb_spi_xfer(CS, [1, (8 + n) << 4, 0])
            #
            # val = ((data[1] << 8) | data[2]) & 0x3FF

            # print(n, ct, val, "data=", [byte for byte in data])
            # print(data[2])

        input("Waiting")


if __name__ == "__main__":
    main()
