from picographics import PicoGraphics, DISPLAY_INKY_PACK

import wifi


PEN_BLACK = 0
PEN_WHITE = 15

display = PicoGraphics(DISPLAY_INKY_PACK)
display.set_pen(PEN_WHITE)
display.clear()
display.set_pen(PEN_BLACK)
display.text("Connecting...", 10, 10)
display.update()

wifi.setup()
display.set_pen(PEN_WHITE)
display.clear()
display.set_pen(PEN_BLACK)
display.text("Connected!", 10, 10)
display.update()

