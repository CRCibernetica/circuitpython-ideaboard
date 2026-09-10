from ideasense import IdeaSense
from font5x5 import TextDisplay
import time

# Initialize hardware and our custom text display
idea = IdeaSense()
display = TextDisplay(idea.matrix)

print("IdeaSense Weather Station Ready!")
print("Press Button A for Temperature")
print("Press Button B for Humidity")
print("Press Button C to Exit")

# Clear the matrix to start
idea.matrix.fill(0)
idea.matrix.show()

while True:
    buttons = idea.pressed
    try:
        # --- BUTTON A: Temperature ---
        if buttons[0]:
            # Format to 1 decimal place (e.g., "24.5 C")
            temp_str = f"{idea.temp:.1f}C"
            print(f"Reading Temp: {temp_str}")
            
            display.scroll_text(temp_str, speed=0.02)
            
            # Clear matrix after scrolling
            idea.matrix.fill(0)
            idea.matrix.show()
            
            # Small debounce delay so it doesn't trigger twice
            time.sleep(1.0)

        # --- BUTTON B: Humidity ---
        elif buttons[1]:
            # Format to 1 decimal place (e.g., "45.2 H")
            humid_str = f"{idea.humid:.1f}H"
            print(f"Reading Humidity: {humid_str}")
            
            display.scroll_text(humid_str, speed=0.02)
            
            idea.matrix.fill(0)
            idea.matrix.show()
            
            time.sleep(1.0)
            
        # --- BUTTON C: Exit ---
        elif buttons[2]:
            print("Exiting...")
            display.scroll_text("BYE", speed=0.02)
            idea.matrix.fill(0)
            idea.matrix.show()
            break  # Break out of the infinite loop
            
        # Tiny sleep to prevent the loop from hogging the CPU
        time.sleep(0.05)

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        idea.matrix.fill(0)
        idea.matrix.show()
        print("\nProgram stopped.")
        break