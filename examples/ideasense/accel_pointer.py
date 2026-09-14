from ideasense import IdeaSense
import time

idea = IdeaSense()

square = (
    "11111",
    "1   1",
    "1   1",
    "1   1",
    "11111"
    )

arrow = (
    "  1  ",
    " 111 ",
    "1 1 1",
    "  1  ",
    "  1  "
    )

cross = (
    "1   1",
    " 1 1 ",
    "  1  ",
    " 1 1 ",
    "1   1"
    )

def transform(shape, action=None):
    if action == "v": # Flip vertical
        return tuple(reversed(shape))
    
    if action == "h": # Flip horizontal
        return tuple("".join(reversed(s)) for s in shape)
    
    if action == "left": # Rotate left
        # Transpose (swap rows/cols) then reverse the columns
        temp = list(zip(*shape))
        transposed = tuple("".join(row) for row in temp)
        return tuple(reversed(transposed))

    if action == "right": # Rotate right
        # Transpose then reverse the internal characters (rows)
        temp = list(zip(*shape))
        return tuple("".join(reversed(row)) for row in temp)

    return shape

def display(shape, action=None):
    # Transform the shape if an action is provided
    processed_shape = transform(shape, action)
    
    for col, bitmap in enumerate(processed_shape):
        for row, pixel in enumerate(bitmap):
            if pixel == "1":
                idea.matrix[row, col] = 1
            else:
                idea.matrix[row, col] = 0

while True:
    x,y,z = idea.accel
    if x > 7:
        display(arrow, action="right")
    elif x < -7:
        display(arrow, action="left")
    elif y > 7:
        display(arrow)
    elif y < -7:
        display(arrow, action="v")
    elif z > 7:
        display(square)
    elif z < -7:
        display(cross)
    idea.matrix.show()