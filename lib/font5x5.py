# font5x5 -- 5x5 pixel font and TextDisplay helper for the IdeaSense matrix.
#
#     from ideasense import IdeaSense
#     from font5x5 import TextDisplay
#     display = TextDisplay(IdeaSense().matrix)
#     display.scroll_text("HELLO")

import time

# A 5x5 alphanumeric font dictionary.
# '1' represents an ON pixel, ' ' represents an OFF pixel.
FONT_5X5 = {
    'A': (" 111 ", "1   1", "11111", "1   1", "1   1"),
    'B': ("1111 ", "1   1", "1111 ", "1   1", "1111 "),
    'C': (" 111 ", "1   1", "1    ", "1   1", " 111 "),
    'D': ("111  ", "1  1 ", "1   1", "1  1 ", "111  "),
    'E': ("11111", "1    ", "1111 ", "1    ", "11111"),
    'F': ("11111", "1    ", "1111 ", "1    ", "1    "),
    'G': (" 111 ", "1    ", "1 111", "1   1", " 111 "),
    'H': ("1   1", "1   1", "11111", "1   1", "1   1"),
    'I': (" 111 ", "  1  ", "  1  ", "  1  ", " 111 "),
    'J': ("    1", "    1", "    1", "1   1", " 111 "),
    'K': ("1   1", "1  1 ", "111  ", "1  1 ", "1   1"),
    'L': ("1    ", "1    ", "1    ", "1    ", "11111"),
    'M': ("1   1", "11 11", "1 1 1", "1   1", "1   1"),
    'N': ("1   1", "11  1", "1 1 1", "1  11", "1   1"),
    'O': (" 111 ", "1   1", "1   1", "1   1", " 111 "),
    'P': ("1111 ", "1   1", "1111 ", "1    ", "1    "),
    'Q': (" 111 ", "1   1", "1   1", "1  1 ", " 11 1"),
    'R': ("1111 ", "1   1", "1111 ", "1  1 ", "1   1"),
    'S': (" 1111", "1    ", " 111 ", "    1", "1111 "),
    'T': ("11111", "  1  ", "  1  ", "  1  ", "  1  "),
    'U': ("1   1", "1   1", "1   1", "1   1", " 111 "),
    'V': ("1   1", "1   1", "1   1", " 1 1 ", "  1  "),
    'W': ("1   1", "1   1", "1 1 1", "11 11", "1   1"),
    'X': ("1   1", " 1 1 ", "  1  ", " 1 1 ", "1   1"),
    'Y': ("1   1", " 1 1 ", "  1  ", "  1  ", "  1  "),
    'Z': ("11111", "   1 ", "  1  ", " 1   ", "11111"),
    
    '0': (" 111 ", "1  11", "1 1 1", "11  1", " 111 "),
    '1': ("  1  ", " 11  ", "  1  ", "  1  ", " 111 "),
    '2': (" 111 ", "    1", " 111 ", "1    ", "11111"),
    '3': (" 111 ", "    1", "  11 ", "    1", " 111 "),
    '4': ("1   1", "1   1", "11111", "    1", "    1"),
    '5': ("11111", "1    ", "1111 ", "    1", "1111 "),
    '6': ("  11 ", " 1   ", "1111 ", "1   1", " 111 "),
    '7': ("11111", "    1", "   1 ", "  1  ", " 1   "),
    '8': (" 111 ", "1   1", " 111 ", "1   1", " 111 "),
    '9': (" 111 ", "1   1", " 1111", "    1", " 11  "),
    
    ' ': ("     ", "     ", "     ", "     ", "     "),
    '!': ("  1  ", "  1  ", "  1  ", "     ", "  1  "),
    '?': (" 111 ", "    1", "  11 ", "     ", "  1  "),
    '.': ("     ", "     ", "     ", "     ", "  1  "),
    
    # Custom Symbols
    '%': ("1   1", "   1 ", "  1  ", " 1   ", "1   1"),
    '°': (" 11  ", "1  1 ", " 11  ", "     ", "     "),
    '@': (" 1 1 ", " 1 1 ", "     ", "1   1", " 111 "), # Smiley Face
    '#': (" 1 1 ", "11111", "11111", " 111 ", "  1  "), # Heart
}

class TextDisplay:
    def __init__(self, matrix):
        """Pass the matrix object from your IdeaSense instance here."""
        self.matrix = matrix

    def show_char(self, char):
        """Displays a single character on the 5x5 matrix without flickering."""
        char = char.upper()
        bitmap = FONT_5X5.get(char, FONT_5X5[' '])
        
        for y, row in enumerate(bitmap):
            for x, val in enumerate(row):
                # Explicitly set 1 or 0 for every pixel to avoid fill() flicker
                self.matrix[x, y] = 1 if val == '1' else 0
                    
        self.matrix.show()

    def scroll_text(self, text, speed=0.1):
        """Smoothly scrolls a string of text across the 5x5 matrix."""
        text = text.upper()
        
        # Initialize 5 empty strings representing the 5 rows
        full_grid = ["", "", "", "", ""]
        
        # Pad the start with blank space so text enters from the right
        for i in range(5):
            full_grid[i] += "     "
            
        # Append each character's bitmap to the full grid + 1 column of spacing
        for char in text:
            bitmap = FONT_5X5.get(char, FONT_5X5[' '])
            for i in range(5):
                full_grid[i] += bitmap[i] + " "
                
        # Pad the end with blank space so text fully exits to the left
        for i in range(5):
            full_grid[i] += "     "
            
        total_columns = len(full_grid[0])
        
        # Slide a 5-column wide "window" across the full text grid
        for offset in range(total_columns - 4):
            for y in range(5):
                for x in range(5):
                    # Fixed: Use the grid character directly to set 1 or 0
                    self.matrix[x, y] = 1 if full_grid[y][offset + x] == '1' else 0
            self.matrix.show()
            time.sleep(speed)