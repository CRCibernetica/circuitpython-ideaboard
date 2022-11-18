import board
from ideaboard import IdeaBoard
from time import sleep

ib = IdeaBoard()

servo_pins = [board.IO4,board.IO5,board.IO18,board.IO19,board.IO23,board.IO25,board.IO26]
servos = []

for i, pin in enumerate(servo_pins):
    servos.append(ib.Servo(pin))

# sweep all servos
for i in range(180):
    for servo in servos:
        print(i)
        servo.angle = i
    sleep(0.01)
        