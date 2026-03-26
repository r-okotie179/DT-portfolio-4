from machine import Pin
import time

led = Pin("LED", Pin.OUT)
l = Pin(15, Pin.OUT)

while True:
    led.on()
    l.on()
    time.sleep(2)
    led.off()
    l.off()
    time.sleep(1)
