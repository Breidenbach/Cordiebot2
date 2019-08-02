'''

TouchButton

Class to process a touch button input
It assumes that no debouncing or pull-up or pull-down resistors are needed.

It returns the number of button presses where the time of the low-level signal
between presses is less than a specified "gap" time.

If the time the button is pressed exceeds 5 seconds, this process returns 255.

'''

import time
from gpiozero import Button

class TouchButton:
    def __init__(self, pin, gap):
        self.button = Button(pin, pull_up=False)
        self.gap = gap
        self.state = 0
        self.button_clock = 0
        self.button_gap = 0
        self.button_count = 0
    def read(self):
        if (not self.button.is_pressed):
            return 0
        self.state = 1
        self.button_count = 1
        self.button_gap = 0
        self.button_clock = time.time()
        while ((time.time() - self.button_clock) < self.gap):
            while (self.state == 1):
                time.sleep(0.1)
                if (not self.button.is_pressed):
                    self.state = 0
                if (time.time() - self.button_clock > 5):
                    self.button_count = 255
                    break
            self.button_clock = time.time()
            while (self.state == 0) and ((time.time() - self.button_clock) < self.gap):
                time.sleep(0.1)
                if self.button.is_pressed:
                    self.state = 1
                    self.button_count += 1
        return self.button_count  
