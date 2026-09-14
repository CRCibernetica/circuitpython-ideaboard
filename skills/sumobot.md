# SumoBot v1: CircuitPython reference for AI code generation

Read this together with `ideaboard.md`. The **SumoBot** (the first version, before the
SumoBot v2) is a CRCibernetica sumo robot built from an IdeaBoard, two DC motors, four
reflective infrared floor sensors wired to header pins, an HC-SR04 ultrasonic sensor
at the front and an LSM6DS3TR-C accelerometer/gyro on I2C. There is **no `sumobot`
library**: everything is read with the `ideaboard` helpers, `hcsr04` and
`adafruit_lsm6ds`, all shipped in `/lib`.

Which robot does the student have? The **v2** has one sensor board under the chassis
that plugs into the STEMMA QT connector and is used through `from sumobotv2 import
SumoBotV2` (see `sumobotv2.md`). The **v1** has separate sensor modules on jumper
wires going to IO32 to IO35, IO25 and IO26. If the student is not sure, ask which one
they see.

Typical use: a robot sumo competition. Two robots on a round black arena (dohyo) with
a white border. A robot loses when pushed out. Robots must stay inside (detect the
white edge), find the opponent (ultrasonic) and push. Many rule sets require a start
delay of about 5 seconds after the start button is pressed.

## 1. The hardware

| Part | Function | Connection |
|---|---|---|
| 4 reflective IR modules | floor sensors, detect the white border | IO33, IO32, IO35, IO34 |
| HC-SR04 | ultrasonic distance to the opponent | TRIG IO26, ECHO IO25 |
| LSM6DS3TR-C | 3-axis accelerometer and gyroscope | I2C, address **0x6B** |
| IdeaBoard L9110S | two DC motors, `ib.motor_1` and `ib.motor_2` | (built in) |
| IdeaBoard WS2812B | status LED, `ib.pixel` | (built in) |

Pins are the ones used by the IdeaScratch Sumobot blocks and the Cenfotec examples.
A robot may be wired differently: put every pin in a named constant at the top of
the program and tell the student to check them against the wires.

Sensor layout, viewed from above, as the IdeaScratch blocks number them:

```
    s1 ----- s2      s1/s2 = front pair, s3/s4 = back pair
     |       |
    s3 ----- s4
```

Confirm on the real robot which pins are the front pair (hold a hand or a white sheet
under each sensor while printing all four) and which motor is left and right.

The IMU is at 0x6B, not the library default 0x6A, so the address must be passed
explicitly. (The IdeaSense Explorer's IMU is at 0x6A, so both can share the bus.)

## 2. Setup

```python
import time
import board
import keypad
from ideaboard import IdeaBoard
from hcsr04 import HCSR04
from adafruit_lsm6ds.lsm6ds3trc import LSM6DS3TRC

ib = IdeaBoard()
keys = keypad.Keys((board.IO0,), value_when_pressed=False)   # BOOT button = start

# --- wiring: check against the robot ---
IR_PINS = (board.IO33, board.IO32, board.IO35, board.IO34)   # s1, s2, s3, s4
TRIG, ECHO = board.IO26, board.IO25

ir = [ib.AnalogIn(p) for p in IR_PINS]
sonar = HCSR04(TRIG, ECHO)
imu = LSM6DS3TRC(board.I2C(), 0x6B)
```

Libraries needed in `/lib` on the board (all in this repository): `ideaboard.py`,
`hcsr04.mpy`, `adafruit_lsm6ds/`, `adafruit_register/`, `adafruit_motor/`,
`neopixel.mpy`, `simpleio.mpy`. Nothing extra has to be installed.

## 3. Sensors

### Infrared floor sensors

The modules are reflective IR pairs (TCRT5000 style) with an emitter, a detector and
usually a comparator with a potentiometer. Two ways to read them:

```python
s1, s2, s3, s4 = [s.value for s in ir]     # analog: 0 to 65535, when AO is wired
```

```python
ir_d = [ib.DigitalIn(p) for p in IR_PINS]  # digital: True/False, when DO is wired
if ir_d[0].value: ...                      # threshold set with the module's potentiometer
```

- Prefer analog when the module's analog output (AO) is wired: the threshold then lives
  in the code and can be calibrated without a screwdriver. `code_IR.py` in the examples
  uses the digital output on IO33.
- Reading four `AnalogIn` values takes well under a millisecond. Read every loop.
- Whether white reads **higher or lower** than black depends on the module. Have the
  student print all four values over black and over white once, then choose a
  `THRESHOLD` halfway between and a comparison direction. Do not assume.
- IO34 and IO35 are input-only pins with no pull resistors. Fine for analog and for a
  module with its own driven digital output. These four pins are not affected by Wi-Fi.

```python
THRESHOLD = 30000                     # from calibration
WHITE_IS_HIGH = False                 # from calibration

def on_white(value):
    return value > THRESHOLD if WHITE_IS_HIGH else value < THRESHOLD

s1, s2, s3, s4 = [s.value for s in ir]
if on_white(s1) or on_white(s2):      # front edge: reverse and turn
    ...
```

### Ultrasonic distance (opponent)

```python
try:
    d = sonar.dist_cm()               # about 2 to 400 cm
except RuntimeError:
    d = None                          # no echo; treat as "nothing in front"
```

- `dist_cm()` blocks until the echo returns, up to a few tens of milliseconds when
  nothing is in range. Call it **once per loop**, not several times, and keep the edge
  check before it.
- Readings jump. Use a limit such as `d is not None and d < 40` for "opponent ahead",
  and require two readings in a row before charging if false triggers are a problem.
- Never `import adafruit_hcsr04` or use `.distance`; that library is not installed.

### Accelerometer and gyroscope

```python
ax, ay, az = imu.acceleration        # m/s^2; flat and still, one axis reads about +/-9.8
gx, gy, gz = imu.gyro                # rad/s; still reads near 0
```

- Detect being lifted or tipped: the axis that normally reads 9.8 drops well below it.
- Detect a collision with the opponent: a spike in `ax`/`ay`.
- Turn by angle and drive straight: integrate the vertical gyro axis (usually `gz`,
  index 2). Print `imu.gyro` while turning the robot by hand to find the axis and its
  sign. The gyro has a small constant offset (drift): measure it while the robot is
  still and subtract it.

```python
import math

def gyro_drift(seconds=2):           # robot must be still
    total, n = 0, 0
    t0 = time.monotonic()
    while time.monotonic() - t0 < seconds:
        total += imu.gyro[2]
        n += 1
        time.sleep(0.005)
    return total / n if n else 0

def turn_degrees(degrees, drift, speed=0.3):
    sign = 1 if degrees > 0 else -1
    target = abs(degrees) - 2        # the robot coasts a little after stopping
    turned = 0
    last = time.monotonic()
    drive(speed * sign, -speed * sign)
    while turned < target:
        now = time.monotonic()
        turned += abs((imu.gyro[2] - drift) * (now - last)) * 180 / math.pi
        last = now
        if target - turned < target / 2:
            drive(0.15 * sign, -0.15 * sign)   # slow down for the second half
        time.sleep(0.005)
    stop()

def drive_straight(speed, seconds, drift, kp=0.15):
    t0 = time.monotonic()
    while time.monotonic() - t0 < seconds:
        error = imu.gyro[2] - drift             # rad/s of unwanted rotation
        correction = max(-0.3, min(0.3, kp * error))
        drive(speed + correction, speed - correction)
        time.sleep(0.01)
    stop()
```

If the robot turns the wrong way or the correction makes it veer more, flip the sign of
`correction` (swap `+` and `-`). These helpers ignore the floor sensors while they run,
so use them for short moves only, or add the edge check inside their loops.

### Status LED

```python
ib.pixel = (0, 0, 255)               # (r, g, b) 0..255: waiting, searching, attacking, edge
```

### Saving data to a file

The IdeaBoard has no USB drive, so code may write files to the board's flash:

```python
with open("datos.csv", "a") as f:
    f.write(f"{time.monotonic()},{d}\n")
```

`code_storage.py` logs ultrasonic readings this way. Read the file back with Thonny,
IdeaCode or `tools/ibserial.py get datos.csv`. Write at most a few times per second
and delete the file when done; flash space and write cycles are limited.

## 4. Motors (from `ideaboard`)

```python
LEFT = ib.motor_1            # swap if the robot turns when told to go straight
RIGHT = ib.motor_2
FWD = 1                      # set to -1 if forward runs backwards

def drive(left, right):      # -1.0 .. 1.0 each
    LEFT.throttle = max(-1, min(1, left * FWD))
    RIGHT.throttle = max(-1, min(1, right * FWD))

def stop():
    LEFT.throttle = 0
    RIGHT.throttle = 0
```

Forward: `drive(0.8, 0.8)`. Spin left: `drive(-0.6, 0.6)`. Reverse: `drive(-0.8, -0.8)`.
Sumo robots usually run at full throttle when pushing; use less while searching.

## 5. Rules for generated code

1. Create `ib`, `keys`, `ir`, `sonar` and `imu` once at the top, with the pins in named
   constants. Do not create sensors that the task does not need.
2. Wait for the BOOT button before moving. Add the competition start delay (usually
   5 s) as a named constant, with `ib.pixel` showing the countdown state.
3. Wrap the main loop in `try/finally` and call `stop()` in `finally`.
4. Read the IR sensors every iteration and check the edge **first**, before the
   ultrasonic sensor or any other behaviour. Staying in the ring beats everything else.
5. Use `time.monotonic()` for manoeuvre timing (reverse for 0.4 s, then turn for 0.3 s)
   rather than long `time.sleep()` calls, so the edge check keeps running. A simple
   state machine (`state = "search" / "attack" / "escape"`) is the right shape.
6. Call `sonar.dist_cm()` at most once per loop and always inside `try/except
   RuntimeError`.
7. Thresholds, sensor pins, which pair is the front, motor direction and gyro sign are
   unknowns: put them in named constants at the top and tell the student how to
   calibrate each one.
8. Loop delay 0.01 to 0.02 s for driving. Faster does not help; the motors and the
   robot's mass are the limit.
9. Follow all rules in `ideaboard.md`.

## 6. Program skeleton

```python
import time
import board
import keypad
from ideaboard import IdeaBoard
from hcsr04 import HCSR04

ib = IdeaBoard()
keys = keypad.Keys((board.IO0,), value_when_pressed=False)

# --- calibrate these ---
IR_PINS = (board.IO33, board.IO32, board.IO35, board.IO34)   # s1, s2 front; s3, s4 back
TRIG, ECHO = board.IO26, board.IO25
THRESHOLD = 30000
WHITE_IS_HIGH = False
OPPONENT_CM = 40
LEFT, RIGHT, FWD = ib.motor_1, ib.motor_2, 1
START_DELAY = 5.0

ir = [ib.AnalogIn(p) for p in IR_PINS]
sonar = HCSR04(TRIG, ECHO)

def drive(l, r):
    LEFT.throttle = max(-1, min(1, l * FWD))
    RIGHT.throttle = max(-1, min(1, r * FWD))

def stop():
    drive(0, 0)

def on_white(v):
    return v > THRESHOLD if WHITE_IS_HIGH else v < THRESHOLD

def opponent_ahead():
    try:
        return sonar.dist_cm() < OPPONENT_CM
    except RuntimeError:
        return False

ib.pixel = (0, 0, 255)
print("Press BOOT to start")
while True:
    e = keys.events.get()
    if e and e.pressed:
        break
    time.sleep(0.01)

ib.pixel = (255, 255, 0)
time.sleep(START_DELAY)
ib.pixel = (0, 255, 0)

state = "search"
until = 0

try:
    while True:
        now = time.monotonic()
        s1, s2, s3, s4 = [s.value for s in ir]

        if on_white(s1) or on_white(s2):          # front edge
            state, until = "escape", now + 0.5
            ib.pixel = (255, 0, 0)
            drive(-1, -1)
        elif on_white(s3) or on_white(s4):        # back edge
            state, until = "escape_fwd", now + 0.5
            ib.pixel = (255, 0, 0)
            drive(1, 1)

        if state in ("escape", "escape_fwd") and now >= until:
            state, until = "turn", now + 0.4
            drive(-0.7, 0.7)
        elif state == "turn" and now >= until:
            state = "search"
        elif state == "search":
            if opponent_ahead():
                ib.pixel = (255, 0, 255)
                drive(1, 1)                       # attack
            else:
                ib.pixel = (0, 255, 0)
                drive(-0.4, 0.4)                  # spin slowly, looking

        time.sleep(0.01)
finally:
    stop()
    ib.pixel = (0, 0, 0)
```

## 7. Examples in this repository

`examples/sumobot/` (by Tomás de Camino Beck, Universidad Cenfotec, comments in
Spanish): `code_IR.py` (one IR module on IO33 as a digital input), `code_ultrasonic.py`
(HC-SR04 on IO26/IO25), `code_acc.py` (LSM6DS3TR-C at 0x6B, acceleration and gyro),
`code_pixel.py` (RGB LED), `code_storage.py` (log ultrasonic readings to `datos.csv`).
Block-based versions of the same robot, including the gyro turn and straight-drive
helpers, are the Sumobot examples in IdeaScratch.
