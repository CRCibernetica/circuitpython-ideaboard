# SumoBot v2 -- measure the surface color on each button press.
#
# Press the BOOT button and the board runs one colour measurement: LED off,
# red, green, blue, reading the detector after each, then hands the LED back.
# About 25 ms.

import board
import keypad

from ideaboard import IdeaBoard
from sumobotv2 import SumoBotV2

ib = IdeaBoard()
sumo = SumoBotV2()

keys = keypad.Keys((board.IO0,), value_when_pressed=False)

REFERENCES = {
    "green": (0.19, 0.52, 0.29),
    "red":   (0.8,0.06,.14),
    "blue":  (.06,.22,.72),
    "yellow": (0.48, 0.41, 0.11),
    "purple": (0.33,0.13,0.53),
    "orange": (0.68,0.17,0.15),
    "desk": (.3, .35, .35),
}

def distance(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5

def classify(sample, refs, max_distance=0.08, min_margin=0.05):
    ranked = sorted((distance(sample, v), name) for name, v in refs.items())
    best_d, best_name = ranked[0]
    if best_d > max_distance:
        return None                     # nothing close enough
    if len(ranked) > 1 and ranked[1][0] - best_d < min_margin:
        return None                     # two references are equally close
    return best_name

print(f"firmware 0x{sumo.firmware:02X}")
print("Ready...")

while True:
    event = keys.events.get()
    if event and event.pressed:
        sample = sumo.color()
        red, green, blue = sample
        #print(f"R={red} G={green} B={blue}")
        x = classify(sample, REFERENCES)
        print(x)


