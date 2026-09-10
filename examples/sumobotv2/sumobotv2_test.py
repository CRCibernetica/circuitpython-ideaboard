# SumoBot v2 -- read everything on the board, once per button press.
#
# The general "is this thing working" example. Press the button on IO0 and it
# prints the IMU, the four IR channels and a colour measurement.

import board
import keypad

from sumobotv2 import SumoBotV2

sumo = SumoBotV2()

keys = keypad.Keys((board.IO0,), value_when_pressed=False)

print("firmware 0x%02X" % sumo.firmware)
print("Ready...")

while True:
    event = keys.events.get()
    if event and event.pressed:
        ax, ay, az = sumo.accel
        gx, gy, gz = sumo.gyro
        s1, s2, s3, s4 = sumo.infrared
        r, g, b = sumo.color()

        print(f"Accel:    {ax:.2f}, {ay:.2f}, {az:.2f}")
        print(f"Gyro:     {gx:.2f}, {gy:.2f}, {gz:.2f}")
        print(f"Infrared: {s1}, {s2}, {s3}, {s4}")
        print(f"Color:    {r:.3f}, {g:.3f}, {b:.3f}")
        print()
