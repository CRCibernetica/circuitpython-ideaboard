"""
button_demo.py - Full demonstration of the IdeaSense button API.

There are two complementary ways to read the three onboard buttons. Both
auto-poll the hardware whenever you access them, so you never need to call
idea.update() yourself.

  1) Event queue
     idea.events.get() returns the next ButtonEvent, or None if the queue is
     empty. Each ButtonEvent has:
         .key_number - 0 (A), 1 (B), or 2 (C)
         .pressed    - True on press, False on release
         .timestamp  - time.monotonic() value at the transition
     Events accumulate in a FIFO (capped at 64) until you drain them, so
     transitions between polls are not lost.

  2) State properties
     Each returns a list [A, B, C] of booleans.
         idea.pressed  - True for ONE tick right after a button goes down
         idea.released - True for ONE tick right after a button goes up
         idea.held     - True for every tick while the button is down

This script exercises all of them in a single loop:

  * Events are drained and logged each iteration (keypad-style).
  * idea.pressed counts total presses per button.
  * idea.released triggers a message when Button B is let go.
  * idea.held drives a "repeat while held" counter on Button C.

Exit by holding A + B + C at the same time.
"""

from ideasense import IdeaSense
import time

idea = IdeaSense()
names = ("A", "B", "C")

press_counts = [0, 0, 0]
c_hold_ticks = 0

print("Press, hold, and release the buttons. Hold A+B+C to exit.\n")

while True:
    time.sleep(0.05)

    # --- 1. Event queue: drain every press/release that arrived this tick ---
    # Using a while-loop to drain means we never miss an event, even if
    # several transitions happened between iterations.
    while True:
        event = idea.events.get()
        if event is None:
            break
        action = "PRESSED" if event.pressed else "RELEASED"
        print(f"[event]    Button {names[event.key_number]} {action} "
              f"at t={event.timestamp:.3f}")

    # --- 2. .pressed: per-tick rising-edge flag ---
    # Equivalent information to a "pressed" event, but in flag form. Handy
    # when you prefer booleans over a queue. Here we count total presses.
    pressed = idea.pressed
    for i, name in enumerate(names):
        if pressed[i]:
            press_counts[i] += 1
            print(f"[pressed]  Button {name} total presses: {press_counts[i]}")

    # --- 3. .released: per-tick falling-edge flag ---
    # Same idea as .pressed but for releases. Demoed on Button B only to
    # keep the output readable.
    if idea.released[1]:
        print("[released] Thanks for releasing Button B!")

    # --- 4. .held: level state while a button is down ---
    # Use this for behavior that should repeat or sustain while held.
    # Cached locally so the exit check below sees the same snapshot.
    held = idea.held
    if held[2]:
        c_hold_ticks += 1
        if c_hold_ticks % 10 == 0:   # roughly every 0.5 s at a 50 ms loop
            print(f"[held]     Button C still held (ticks={c_hold_ticks})")
    else:
        c_hold_ticks = 0

    # Exit condition: all three buttons held at once.
    if all(held):
        print("\nAll three buttons held - exiting.")
        break
