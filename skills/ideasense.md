# IdeaSense Explorer: CircuitPython reference for AI code generation

Read this together with `ideaboard.md`. The **IdeaSense Explorer** is a sensor and
display board from CRCibernetica that plugs into the IdeaBoard's STEMMA QT / QWIIC
connector (I2C). The IdeaBoard runs the code; the IdeaSense provides the matrix,
buttons and sensors. All of it is exposed through one Python object, `IdeaSense`.

## 1. The hardware

Four I2C devices on one board, all handled by the library:

| Part | Function | I2C address |
|---|---|---|
| HT16K33 | 5x5 LED matrix and the three buttons A, B, C | 0x70 |
| SHT30 | temperature and humidity | 0x44 |
| LTR303 | ambient light (visible + infrared) | 0x29 |
| LSM6DS3TR-C | 3-axis accelerometer and 3-axis gyroscope | 0x6A |

The matrix is 5 columns by 5 rows, single colour, each pixel on or off.

## 2. Setup

```python
import time
from ideasense import IdeaSense

idea = IdeaSense()
```

Create `idea = IdeaSense()` once. If the project also needs the IdeaBoard's own
features (motors, servos, pins, RGB LED), add `from ideaboard import IdeaBoard` and
`ib = IdeaBoard()`; the two do not conflict. `IdeaSense()` opens the I2C bus itself
with `board.I2C()`. If the board is not plugged in, the constructor raises
`ValueError: No I2C device at address`.

Libraries needed in `CIRCUITPY/lib/` (all included in this repository):
`ideasense.py`, `font5x5.py`, `adafruit_ht16k33/`, `adafruit_sht31d.mpy`,
`adafruit_ltr329_ltr303.mpy`, `adafruit_lsm6ds/`, `adafruit_register/`.

## 3. API

### Matrix

```python
idea.matrix.fill(0)          # all off (1 = all on)
idea.matrix[x, y] = 1        # x = column 0..4 left to right, y = row 0..4 top to bottom
idea.matrix[2, 2] = 0        # centre pixel off
idea.matrix.brightness(0.5)  # 0.0 to 1.0; a METHOD call, not an assignment. Default 0.3
idea.matrix.show()           # push the drawing to the LEDs
```

- Coordinates outside 0 to 4 raise `ValueError`. Clamp or check before drawing.
- Pixels **cannot be read back** (`idea.matrix[x, y]` on the right-hand side fails).
  Keep your own 5x5 list of lists as the frame buffer and redraw it each loop.
- Pattern for drawing an icon:

```python
HEART = [
    "01010",
    "11111",
    "11111",
    "01110",
    "00100",
]

def draw(rows):
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            idea.matrix[x, y] = 1 if ch == "1" else 0
    idea.matrix.show()

draw(HEART)
```

- A bar graph: light `y` rows from the bottom, `for y in range(4, 4 - level, -1)`.
- Animation: redraw the whole frame each iteration, then `time.sleep(0.05 to 0.2)`.
  Draw every pixel explicitly (1 or 0) rather than `fill(0)` then drawing, to avoid
  flicker.

### Text on the matrix (`font5x5`)

```python
from font5x5 import TextDisplay
display = TextDisplay(idea.matrix)

display.show_char("A")                       # one character, stays on screen
display.scroll_text("HOLA 25.3C", speed=0.08) # scrolls right to left, blocks until done
```

- Font covers A to Z, 0 to 9, space and `! ? . % ° @ #`. Lower case is converted to
  upper case. Unknown characters print as blanks.
- `speed` is the delay per column in seconds; 0.05 is fast, 0.15 is slow. The scroll
  is blocking: buttons and sensors are not read while it runs. Keep messages short.
- Show numbers with formatting: `f"{idea.temp:.1f}C"`.

### Sensors

```python
t = idea.temp        # degrees Celsius, float
h = idea.humid       # relative humidity in %, float
lux = idea.light     # visible + IR light, integer counts (bigger = brighter; not real lux)
ax, ay, az = idea.accel   # m/s^2. Flat and still: one axis reads about +/-9.8
gx, gy, gz = idea.gyro    # rad/s. Still: all near 0
```

- Temperature reads a degree or two high after the board has been powered for a while
  (self-heating). Fine for trends and thresholds.
- Light values depend on the room; read a few and choose thresholds from what you see.
  Typical: dark room tens, indoor hundreds to a few thousand, sunlight much higher.
- Tilt detection: compare `ax` and `ay` against a threshold around 1.5 to 3 m/s².
  Which axis is "left/right" depends on how the board is held; tell the student to
  print `idea.accel` and tilt it to find out.
- Shake detection: total acceleration `math.sqrt(ax*ax + ay*ay + az*az)` far from 9.8.
- Rotation: integrate a gyro axis over time (`angle += gz * dt`) for approximate turning.

### Buttons A, B, C

Button numbers: A = 0, B = 1, C = 2. Two ways to read them; both poll the hardware
automatically, so `idea.update()` is never needed.

Event queue (recommended for "do something once per press"):

```python
while True:
    event = idea.events.get()          # ButtonEvent or None
    if event and event.pressed:
        if event.key_number == 0:
            print("A pressed")
    time.sleep(0.01)
```

`ButtonEvent` has `.key_number` (0, 1, 2), `.pressed` (True on press, False on release)
and `.timestamp`. Events queue up (max 64) so none are lost between polls.
`idea.events.clear()` empties the queue; `len(idea.events)` counts waiting events.

State lists, each `[A, B, C]` of booleans:

```python
pressed = idea.pressed    # True for one loop iteration at the moment of pressing
released = idea.released  # True for one loop iteration at the moment of release
held = idea.held          # True the whole time the button is down
```

Rules:
- Read each property **once per loop** into a variable, then use that variable.
  Reading `idea.pressed` twice with time in between can miss the press.
- Poll at least every 50 ms (`time.sleep(0.05)` or less) for responsive buttons.
- Release is reported about 0.15 s after the finger lifts (hardware latch timing).
  Do not build anything that needs precise release timing.
- Use `held` for "repeat while holding" (e.g. increase a counter every 0.2 s).
- Blocking calls like `scroll_text()` pause button reading; presses made during a
  scroll are queued in `events` but `pressed` will not see them.

## 4. Rules for generated code

1. Create `idea = IdeaSense()` once. Do not also create `Matrix8x8`, `SHT31D`,
   `LTR303` or `LSM6DS3TRC` objects yourself; the library owns them.
2. Use `idea.matrix.brightness(0.3)` as a call. `idea.matrix.brightness = 0.3` silently
   breaks the method.
3. Coordinates are `[x, y]` with `(0, 0)` top left, both 0 to 4.
4. Keep a frame buffer in Python if the program needs to know what is lit.
5. Do not draw during time-critical sensor reads; drawing 25 pixels takes several
   milliseconds of I2C traffic.
6. When reading temperature, humidity and light for display, read once per second or
   slower. The IMU can be read every loop.
7. Sensors return floats; format them with `:.1f` before showing.
8. Follow all rules in `ideaboard.md` (sleep in every loop, complete programs, etc.).

## 5. Project patterns

Weather display on button press (from `examples/ideasense/weather_station.py`):

```python
import time
from ideasense import IdeaSense
from font5x5 import TextDisplay

idea = IdeaSense()
display = TextDisplay(idea.matrix)

while True:
    pressed = idea.pressed
    if pressed[0]:
        display.scroll_text(f"{idea.temp:.1f}C", speed=0.05)
    elif pressed[1]:
        display.scroll_text(f"{idea.humid:.0f}%", speed=0.05)
    time.sleep(0.05)
```

Light-level bar graph, updated continuously:

```python
level = int(min(5, idea.light / 200))      # 0..5, adjust 200 to the room
for y in range(5):
    for x in range(5):
        idea.matrix[x, y] = 1 if y >= 5 - level else 0
idea.matrix.show()
```

Tilt ball: keep `(bx, by)` in Python, move it by the sign of `ax`/`ay` when past a
threshold, clamp to 0 to 4, redraw. `examples/ideasense/sand.py` does this with ten
grains that collide.

Menu with A/B to choose and C to confirm: keep an `index` variable, change it on
`event.key_number` 0 or 1, act on 2. Show the index as a digit with `show_char`.

Combining with the IdeaBoard: the IdeaSense can be the "dashboard" of a robot. E.g.
show the ultrasonic distance as a bar, use A/B/C to choose speed, drive with
`ib.motor_1.throttle`.

## 6. Examples in this repository

`examples/ideasense/`: `ideasense_simpletest.py` (every feature once), `button_test.py`
(event queue), `button_demo.py` (all button APIs in one loop), `text_demo.py` (font and
scrolling), `weather_station.py`, `sand.py` (accelerometer game). `README.md` in the
same folder is the human-readable API description.
