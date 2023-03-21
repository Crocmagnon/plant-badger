import time
import machine
from pimoroni_i2c import PimoroniI2C
from pcf85063a import PCF85063A
import ntptime

import badger2040


class Badger2040(badger2040.Badger2040):
    def __init__(self):
        super().__init__()
        i2c = PimoroniI2C(sda=4, scl=5)
        self.rtc = PCF85063A(i2c)

    def halt(self):
        time.sleep(0.05)
        enable = machine.Pin(badger2040.ENABLE_3V3, machine.Pin.OUT)
        enable.off()
        while not self.pressed_any() and not self.rtc.read_timer_flag():
            pass

    def set_clocks(self):
        ntptime.settime()
        now = time.localtime()
        self.rtc.datetime(now[:7])
