import board
import time
from ideaboard import IdeaBoard

ib = IdeaBoard()

#Digital In
# entrada = ib.DigitalIn(board.IO27, pull=UP)
# pull can be UP or DOWN, default None)
entrada = ib.DigitalIn(board.IO27)
while True:
    print(entrada.value)
    time.sleep(0.5)