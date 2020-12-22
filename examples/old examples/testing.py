from RPi import GPIO
from functools import partial


# rotary encoder setup
clk = 19
dt = 26

GPIO.setmode(GPIO.BCM)
# set to GPIO.PUD_UP as the TEAC panel uses an encoder that is grounded
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

counter = 0
clkLastState = GPIO.input(clk)


def volume(counter, pin):
    print(counter)
    print(pin)

    if pin==19:
        counter -= 1
        print(str(counter))
        return counter
    if pin==26:
        counter += 1
        print(str(counter))
        return counter
    else:
        print("Something  isn't right")

vol_up=partial(volume, counter)
vol_down=partial(volume, counter)

GPIO.add_event_detect(dt, GPIO.BOTH, callback=vol_up)
GPIO.add_event_detect(clk, GPIO.BOTH, callback=vol_down)


input("Waiting...")