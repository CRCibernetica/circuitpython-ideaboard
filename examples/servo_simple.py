import board
from ideaboard import IdeaBoard
from time import sleep

ib = IdeaBoard()

servo1 = ib.Servo(board.IO4)
# servo2 = ib.Servo(board.IO5, min_pulse = 500, max_pulse = 2500)

while True:
    # Set servo angle to 10 degrees
    servo1.angle = 10
    sleep(2)
    # Set servo angle to 170 degrees
    servo1.angle = 170
    sleep(2)