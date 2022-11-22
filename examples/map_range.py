import board
from ideaboard import IdeaBoard
from analogio import AnalogIn

ib = IdeaBoard()

pot = AnalogIn(board.IO33)

servo = ib.Servo(board.IO4)

while True:
    val = pot.value
    val = ib.map_range(val, 0, 65535, 0, 180)
    servo.angle = val