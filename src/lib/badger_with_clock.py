import time
import machine
from pimoroni_i2c import PimoroniI2C
from pcf85063a import PCF85063A
import ntptime
import random

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

    def set_timer_minutes(self, minutes: int):
        """Wake the board in X minutes. Doesn't halt the board."""
        self.rtc.clear_timer_flag()
        self.rtc.set_timer(minutes, ttp=PCF85063A.TIMER_TICK_1_OVER_60HZ)
        self.rtc.enable_timer_interrupt(True)

    def set_timer_minutes_with_jitter(
        self, minutes: int, jitter_percentage: float = 0.2
    ):
        """
        Wake the board in X minutes with some jitter. Doesn't halt the board.
        jitter_percentage should be a float between 0.0 and 1.0.
        """
        delta = int(minutes * abs(jitter_percentage))
        minutes += random.randint(-delta, delta)
        self.set_timer_minutes(minutes)
