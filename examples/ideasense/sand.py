import time
import random
from ideasense import IdeaSense

# Initialize the hardware
idea = IdeaSense()

# Simulation Constants
WIDTH = 5
HEIGHT = 5
GRAIN_COUNT = 10  # How many grains of sand to start with

# Initialize sand positions: [(x1, y1), (x2, y2), ...]
sand_grains = []
while len(sand_grains) < GRAIN_COUNT:
    pos = (random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1))
    if pos not in sand_grains:
        sand_grains.append(list(pos))

def get_target_deltas(ax, ay):
    """Translates accelerometer readings into movement directions."""
    # Threshold to prevent jittering when level
    dx = 0
    if ax > 1.5: dx = -1
    elif ax < -1.5: dx = 1
    
    dy = 0
    if ay > 1.5: dy = 1
    elif ay < -1.5: dy = -1
    
    return dx, dy

while True:
    # 1. Get tilt data
    accel_x, accel_y, _ = idea.accel
    dx, dy = get_target_deltas(accel_x, accel_y)

    # 2. Update grain positions
    if dx != 0 or dy != 0:
        new_sand_grains = []
        # Create a occupied map for quick collision checking
        occupied = set(tuple(p) for p in sand_grains)

        for grain in sand_grains:
            curr_x, curr_y = grain
            
            # Calculate potential new spot
            next_x = max(0, min(WIDTH - 1, curr_x + dx))
            next_y = max(0, min(HEIGHT - 1, curr_y + dy))
            
            # If the spot is free, move there
            if (next_x, next_y) not in occupied:
                occupied.remove((curr_x, curr_y))
                occupied.add((next_x, next_y))
                new_sand_grains.append([next_x, next_y])
            else:
                # If blocked, stay put
                new_sand_grains.append([curr_x, curr_y])
        
        sand_grains = new_sand_grains

    # 3. Render to the IdeaSense Matrix
    idea.matrix.fill(0)
    for x, y in sand_grains:
        # Drawing on the matrix
        idea.matrix[x, y] = 1
    
    idea.matrix.show()

    # Small delay for smooth animation
    time.sleep(0.1)