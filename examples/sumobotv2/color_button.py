# SumoBot v2 -- measure the surface colour on each button press.
#
# Press the button on IO0 and the board runs one colour measurement: LED off,
# red, green, blue, reading the detector after each, then hands the LED back.
# About 25 ms.
#
# Both forms are printed. color() is the one to use -- dark subtracted and
# divided by the total, so it stays put as the sensor's height changes.
# raw_color() is the underlying counts, worth watching for clipping.
#
# HOW TO RUN: hold the sensor over a surface and press the button.

import board
import keypad

from sumobotv2 import SumoBotV2

sumo = SumoBotV2()

keys = keypad.Keys((board.IO0,), value_when_pressed=False)

sumo.led = (0, 0, 0)   # LED idle and dark between measurements

print("firmware 0x%02X, illumination %d" % (sumo.firmware, sumo.illumination))
print("Ready...")

while True:
    event = keys.events.get()
    if event and event.pressed:
        dark, red, green, blue = sumo.raw_color()

        r = max(0, red - dark)
        g = max(0, green - dark)
        b = max(0, blue - dark)
        total = r + g + b

        print(f"counts:     dark={dark} R={red} G={green} B={blue}")
        if total:
            print(f"above dark: R={r} G={g} B={b}")
            print(f"color:      {r / total:.3f}, {g / total:.3f}, {b / total:.3f}")
        else:
            print("color:      no reflected light")

        if max(red, green, blue) > 1000:
            print("WARNING: a channel is near 1023 -- the ADC is clipping.")
            print("         Lower sumo.illumination, but read its docstring first.")
        print()
