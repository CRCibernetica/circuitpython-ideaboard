# Tomás de Camino Beck
# Escuela de Sistemas Inteligentes
# Universidad Cenfotec

# Ejemplo de uso del sensor infrarrojo conectado al IO33

import board
from ideaboard import IdeaBoard
import time

ib = IdeaBoard()
irSensor = ib.DigitalIn(board.IO33)

while True:
    print(irSensor.value)
    time.sleep(0.5)