from ideaboard import IdeaBoard
from time import sleep_ms

ib = IdeaBoard()

# ib.acroiris(0-255) creates a color wheel
# from 0 (RED) to 255 (RED)
while True:
    for i in range(256):
        ib.arcoiris(i)
        print(i)
        sleep(0.05)
