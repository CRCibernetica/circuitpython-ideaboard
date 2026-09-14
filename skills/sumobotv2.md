# SumoBot v2: CircuitPython reference for AI code generation

Read this together with `ideaboard.md`. The **SumoBot v2** is a CRCibernetica sumo
robot: an IdeaBoard drives two motors, and a sensor board underneath reads four
infrared floor sensors, a reflective colour sensor and an accelerometer/gyro. The
sensor board connects to the IdeaBoard over I2C (STEMMA QT). The `sumobotv2` library
exposes all sensors through one object, `SumoBotV2`. Motors are driven with the
`ideaboard` library. The earlier SumoBot with separate sensor modules on jumper wires
is a different robot: see `sumobot.md`.

Typical use: a robot sumo competition. Two robots on a round black arena (dohyo) with
a white border. A robot loses when pushed out. Robots must stay inside (detect the
white edge), find the opponent, and push. Many rule sets require a start delay of
about 5 seconds after the start button is pressed.

## 1. The hardware

| Part | Function | I2C address |
|---|---|---|
| CH32V003 sensor board | 5 analog channels (4 IR + colour detector), one WS2812B RGB LED | 0x34 |
| LSM6DS3TR-C | 3-axis accelerometer and gyroscope | 0x6B |
| IdeaBoard L9110S | two DC motors, `ib.motor_1` and `ib.motor_2` | (not I2C) |

Infrared sensor layout, viewed from above, as the library numbers them:

```
    s1 ----- s2      s1/s2 are one pair (front), s3/s4 the other (back)
     |       |       s2/s4 are one side (right), s1/s3 the other (left)
    s3 ----- s4
```

Confirm on the real robot which pair faces forward: read `sumo.infrared` while holding
a hand under each sensor. Likewise confirm which motor is left and which is right.
Write the answer once as named constants at the top of the program.

## 2. Setup

```python
import time
import board
import keypad
from ideaboard import IdeaBoard
from sumobotv2 import SumoBotV2

ib = IdeaBoard()
sumo = SumoBotV2()
keys = keypad.Keys((board.IO0,), value_when_pressed=False)   # BOOT button = start
```

`SumoBotV2()` raises `RuntimeError` if the sensor board is not found or its firmware
is older than 0x08. Libraries needed in `/lib` on the board (all in this repository):
`sumobotv2.py`, `ideaboard.py`, `adafruit_lsm6ds/`, `adafruit_register/`,
`adafruit_motor/`, `neopixel.mpy`, `simpleio.mpy`.

## 3. API

### Infrared floor sensors

```python
s1, s2, s3, s4 = sumo.infrared      # each 0 to 1023, all read in one I2C transaction
values = sumo.analog                # [s1, s2, s3, s4, s5]; s5 is the colour detector
```

- Fast (well under a millisecond). Read every loop iteration.
- All four values come from the same instant, so comparisons between sensors are fair.
- Whether the white border reads **higher or lower** than the black arena depends on the
  sensors. Have the student print `sumo.infrared` over black and over white once, then
  pick a `THRESHOLD` halfway between and a comparison direction. Do not assume.
- Edge detection pattern:

```python
THRESHOLD = 500                       # from calibration
WHITE_IS_HIGH = True                  # from calibration

def on_white(value):
    return value > THRESHOLD if WHITE_IS_HIGH else value < THRESHOLD

s1, s2, s3, s4 = sumo.infrared
if on_white(s1) or on_white(s2):      # front edge: reverse and turn
    ...
```

### Direction of a brightness gradient (`ir_gradient`)

`examples/sumobotv2/ir_gradient.py` provides `ir_gradient(sumo.infrared)` returning
`(x, y, strength, degrees)`: the direction towards higher readings, normalized so
lighting changes do not matter. Check `strength` against a noise floor before trusting
`degrees`. Copy the file to `/` or `/lib` on the board to import it.

### Colour sensor

```python
r, g, b = sumo.color()       # fractions 0.0 to 1.0 that sum to 1; (0,0,0) if nothing reflects
dark, red, green, blue = sumo.raw_color()   # raw counts 0..1023, for calibration
```

- `color()` blocks for about 30 to 60 ms: the board flashes its LED red, green and
  blue in turn and reads the detector after each, then restores the indicator colour.
  Call it when needed (e.g. once per loop at 10 Hz, or on demand), not thousands of
  times per second.
- The result is a **proportion**, so it stays the same as the sensor height changes.
  Compare against stored references with a distance function:

```python
REFERENCES = {                        # measure these on the real surfaces
    "green":  (0.19, 0.52, 0.29),
    "red":    (0.80, 0.06, 0.14),
    "blue":   (0.06, 0.22, 0.72),
    "yellow": (0.48, 0.41, 0.11),
    "black":  (0.33, 0.33, 0.33),
}

def distance(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5

def classify(sample, refs, max_distance=0.08, min_margin=0.05):
    ranked = sorted((distance(sample, v), name) for name, v in refs.items())
    best_d, best_name = ranked[0]
    if best_d > max_distance:
        return None                   # nothing close
    if len(ranked) > 1 and ranked[1][0] - best_d < min_margin:
        return None                   # ambiguous
    return best_name
```

- Calibrate by printing `sumo.color()` over each surface a few times and copying the
  averages into `REFERENCES`. Grey, black and white all give roughly (0.33, 0.33,
  0.33); tell them apart with `raw_color()` totals or with `sumo.detector`.
- If any channel of `raw_color()` is near 1023 the detector is saturated; only then
  lower `sumo.illumination` (0 to 255, default 255). Otherwise leave it at 255:
  intermediate levels, especially around 128, give unreliable readings.
- `sumo.detector` is s5 as a plain light level with the LED as you left it.

### LED

```python
sumo.led = (255, 0, 0)       # indicator colour (r, g, b) 0..255; borrowed briefly by color()
sumo.led = (0, 0, 0)
```

Useful for showing the robot's state (searching, attacking, edge). It is separate from
the IdeaBoard's own `ib.pixel`.

### IMU

```python
ax, ay, az = sumo.accel      # m/s^2; flat and still one axis reads about +/-9.8
gx, gy, gz = sumo.gyro       # rad/s; still reads near 0
```

- Detect being lifted or tipped: the axis that normally reads 9.8 drops well below it.
- Detect collision with the opponent: a spike in `ax`/`ay`.
- Turn by angle: integrate the vertical gyro axis, `angle += gz * dt`, with
  `dt = time.monotonic() - last`. Print `sumo.gyro` while turning to find which axis
  is vertical and its sign. Drift is a few degrees per minute; fine for a single turn.

### Misc

```python
sumo.firmware                # sensor board firmware revision, integer (needs >= 0x08)
sumo.last_color_frame        # (dark, red, green, blue, count) from the last measurement
```

## 4. Motors (from `ideaboard`)

```python
LEFT = ib.motor_1            # swap if the robot turns when told to go straight
RIGHT = ib.motor_2
FWD = 1                      # set to -1 if forward runs backwards

def drive(left, right):      # -1.0 .. 1.0 each
    LEFT.throttle = left * FWD
    RIGHT.throttle = right * FWD

def stop():
    LEFT.throttle = 0
    RIGHT.throttle = 0
```

Forward: `drive(0.8, 0.8)`. Spin left: `drive(-0.6, 0.6)`. Reverse: `drive(-0.8, -0.8)`.
Sumo robots usually run at full throttle when pushing; use less while searching.

## 5. Rules for generated code

1. Create `ib`, `sumo` and `keys` once at the top. Never read the I2C devices directly.
2. Wait for the BOOT button before moving. Add the competition start delay (usually
   5 s) as a named constant, with the LED showing the countdown state.
3. Wrap the main loop in `try/finally` and call `stop()` in `finally`.
4. Read `sumo.infrared` every iteration and check the edge **first**, before any other
   behaviour. Staying in the ring beats everything else.
5. Use `time.monotonic()` for manoeuvre timing (e.g. reverse for 0.4 s, then turn for
   0.3 s) rather than long `time.sleep()` calls, so the edge check keeps running.
   A simple state machine (`state = "search" / "attack" / "escape"`) is the right shape.
6. Do not call `sumo.color()` inside the fast drive loop unless the task is about
   colour. It costs 30 to 60 ms per call.
7. Thresholds, sensor orientation and motor direction are unknowns: put them in named
   constants at the top and tell the student how to calibrate each one.
8. Loop delay 0.01 to 0.02 s for driving. Faster does not help; the motors and the
   robot's mass are the limit.
9. Follow all rules in `ideaboard.md`.

## 6. Program skeleton

```python
import time
import board
import keypad
from ideaboard import IdeaBoard
from sumobotv2 import SumoBotV2

ib = IdeaBoard()
sumo = SumoBotV2()
keys = keypad.Keys((board.IO0,), value_when_pressed=False)

# --- calibrate these ---
THRESHOLD = 500
WHITE_IS_HIGH = True
LEFT, RIGHT, FWD = ib.motor_1, ib.motor_2, 1
START_DELAY = 5.0

def drive(l, r):
    LEFT.throttle = l * FWD
    RIGHT.throttle = r * FWD

def stop():
    drive(0, 0)

def on_white(v):
    return v > THRESHOLD if WHITE_IS_HIGH else v < THRESHOLD

sumo.led = (0, 0, 255)
print("Press BOOT to start")
while True:
    e = keys.events.get()
    if e and e.pressed:
        break
    time.sleep(0.01)

sumo.led = (255, 255, 0)
time.sleep(START_DELAY)
sumo.led = (0, 255, 0)

state = "search"
until = 0

try:
    while True:
        now = time.monotonic()
        s1, s2, s3, s4 = sumo.infrared

        if on_white(s1) or on_white(s2):          # front edge
            state, until = "escape", now + 0.5
            drive(-1, -1)
        elif on_white(s3) or on_white(s4):        # back edge
            state, until = "escape_fwd", now + 0.5
            drive(1, 1)

        if state in ("escape", "escape_fwd") and now >= until:
            state, until = "turn", now + 0.4
            drive(-0.7, 0.7)
        elif state == "turn" and now >= until:
            state = "search"
        elif state == "search":
            drive(0.6, 0.6)                       # replace with opponent-finding logic

        time.sleep(0.01)
finally:
    stop()
    sumo.led = (0, 0, 0)
```

## 7. Examples in this repository

`examples/sumobotv2/`: `sumobotv2_simpletest.py` (every feature once),
`sumobotv2_test.py` (read everything per button press), `color_button.py` (colour
measurement per press, raw and normalized), `color_normalized.py` (classify colour
against references), `continuous_test.py` (classify continuously), `ir_gradient.py`
(direction from the four IR sensors).
