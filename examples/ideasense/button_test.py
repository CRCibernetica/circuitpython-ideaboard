from ideasense import IdeaSense
import time

idea = IdeaSense()
names = ("A", "B", "C")

while True:
    time.sleep(0.01)
    event = idea.events.get()
    if event:
        action = "pressed" if event.pressed else "released"
        print(f"Button {names[event.key_number]} {action}")
