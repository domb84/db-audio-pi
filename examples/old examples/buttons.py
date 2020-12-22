from RPi import GPIO
import time

# The wiring for the Teac T-H300DABmkII buttons / rotary is as follows:
# 1 : GND (BLACK WIRE)
# 2 : GPIO 19 (ROTARY DOWN)
# 3 : GPIO 26 (ROTARY UP)
# 4 : 3.V (POWER LED)
# 5 : GPIO 20 (POWER, DIMMER, MEM, AUTO TUN, ENTER, FUNC, INFO, BAND)
# 6 : GPIO 21 (TIMER, TIME ADJ, DAILY)
# 7 : NOT USED
# 8 : NOT USED


dt=22

GPIO.setmode(GPIO.BCM)
# set to GPIO.PUD_UP as the TEAC panel uses buttons that are grounded
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

current_state=str(GPIO.input(dt))
print("Starting GPIO input state is " + current_state)

def buttonPress(channel):
    new_state=str(GPIO.input(dt))
    press_time=time.time()

    print("Button pressed GPIO input state is " + new_state)
    # measurement = 0
    while GPIO.input(dt) == GPIO.LOW:
        charge_time = time.time()
        # measurement += 1

    final_state=str(GPIO.input(dt))
    print(final_state)
    if final_state=="1":
        total_time=charge_time-press_time
        print("Final GPIO input state is " + final_state + " time taken " + str(total_time))
    else:
        print("GPIO never returned to HIGH")

GPIO.add_event_detect(dt, GPIO.FALLING, callback=buttonPress, bouncetime=500)

input("Listening...")

GPIO.cleanup()           # clean up GPIO on normal exits