import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)

LDR_PIN = 29  # Pin for LDR
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LDR_PIN, GPIO.IN)

# IR sensors
sensor1 = 7
sensor2 = 13
sensor3 = 18

# LEDs
leds1 = [11, 12]
leds2 = [15, 16]
leds3 = [22, 23]

# Setup IR sensors
GPIO.setup(sensor1, GPIO.IN)
GPIO.setup(sensor2, GPIO.IN)
GPIO.setup(sensor3, GPIO.IN)

# Setup LEDs
for pin in leds1 + leds2 + leds3:
    GPIO.setup(pin, GPIO.OUT)

try:
    while True:
        light_status = GPIO.input(LDR_PIN)
        print(f"LDR Status: {light_status}")

        if light_status == 0:
            print("Bright Light Detected - All LEDs OFF")
            for pin in leds1 + leds2 + leds3:
                GPIO.output(pin, GPIO.LOW)

        else:
            # Only respond to sensors when it's dark
            val1 = GPIO.input(sensor1)
            print(f"Sensor 1: {val1}")
            GPIO.output(leds1[0], GPIO.HIGH if val1 == 0 else GPIO.LOW)
            GPIO.output(leds1[1], GPIO.HIGH if val1 == 0 else GPIO.LOW)

            val2 = GPIO.input(sensor2)
            print(f"Sensor 2: {val2}")
            GPIO.output(leds2[0], GPIO.HIGH if val2 == 0 else GPIO.LOW)
            GPIO.output(leds2[1], GPIO.HIGH if val2 == 0 else GPIO.LOW)

            val3 = GPIO.input(sensor3)
            print(f"Sensor 3: {val3}")
            GPIO.output(leds3[0], GPIO.HIGH if val3 == 0 else GPIO.LOW)
            GPIO.output(leds3[1], GPIO.HIGH if val3 == 0 else GPIO.LOW)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Cleaning up GPIO...")
    GPIO.cleanup()
