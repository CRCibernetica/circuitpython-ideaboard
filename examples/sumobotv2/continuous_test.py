# SumoBot v2 -- measure the surface colour continiously


import board
import keypad
import time

from ideaboard import IdeaBoard
from sumobotv2 import SumoBotV2

ib = IdeaBoard()
sumo = SumoBotV2()

sumo.led = (0, 0, 0)

REFERENCES = {
    "green": (0.156, 0.527, 0.317),
    "red":   (.7,.15,.15),
    "blue":  (.1,.3,.6),
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

print("firmware 0x%02X, illumination %d" % (sumo.firmware, sumo.illumination))
print("Ready...")

interval = 0.3
last = time.monotonic()
while True:
    now = time.monotonic()
    if now - last > interval:
        sample = sumo.color()
        x = classify(sample, REFERENCES)
        print(x)


