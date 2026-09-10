from ideasense import IdeaSense
from font5x5 import TextDisplay
import time

# Initialize hardware
idea = IdeaSense()

# Initialize our new text display, passing in the IdeaSense matrix
display = TextDisplay(idea.matrix)

print("Displaying single characters...")
display.show_char('H')
time.sleep(1)
display.show_char('I')
time.sleep(1)
display.show_char('!')
time.sleep(1)

print("Scrolling text...")
# Scroll a message smoothly across the 5x5 matrix
display.scroll_text("HELLO CENFOTEC", speed=0.08)

# Clear the screen at the end
idea.matrix.fill(0)
idea.matrix.show()