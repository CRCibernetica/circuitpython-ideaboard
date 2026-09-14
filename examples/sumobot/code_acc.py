from ideaboard import IdeaBoard
import time
import board
from adafruit_lsm6ds.lsm6ds3trc import LSM6DS3TRC


ib = IdeaBoard()
i2c = board.I2C()
sensor = LSM6DS3TRC(i2c, 0x6b)


while True:
    print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % (sensor.acceleration))
    print("Gyro X:%.2f, Y: %.2f, Z: %.2f radians/s" % (sensor.gyro))
    print("")
    time.sleep(0.5)