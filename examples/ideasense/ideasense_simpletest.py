from ideasense import IdeaSense
import time

idea = IdeaSense()


idea.matrix.fill(0)       # Clear screen
idea.matrix[0, 0] = 1     # Example: Set top left pixel (x=0, y=0) to on
idea.matrix.show()        # Push changes to display

print(f"Temp: {idea.temp}")
print(f"Humid: {idea.humid}")
print(f"Light: {idea.light}")
print(f"Accel: {idea.accel}")
print(f"Gyro: {idea.gyro}")

while True:
    # idea.pressed fires once per push; use idea.held for repeating input while a button is down
    buttons = idea.pressed
    if buttons[0]:
        print("Button A")
    elif buttons[1]:
        print("Button B")
    elif buttons[2]:
        print("Button C")
    time.sleep(0.05)
