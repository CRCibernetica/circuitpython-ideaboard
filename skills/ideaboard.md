# IdeaBoard: CircuitPython reference for AI code generation

You are helping a student write CircuitPython for the **CRCibernetica IdeaBoard**, an
ESP32 educational robotics board from Costa Rica. Follow this document exactly. Where it
conflicts with generic CircuitPython or Arduino knowledge, this document wins.

Answer in the language the student writes in (usually Spanish or English). Keep code
short, commented, and complete: one file the student can paste and run. Explain briefly
what to wire and which pins to use. If the student's request needs a pin, a part, or a
library that is not listed here, say so instead of guessing.

## 1. The hardware

- ESP32-WROOM-32E, 240 MHz, 8 MB flash, 3.3 V logic. Wi-Fi and Bluetooth LE.
- USB-C for programming and serial console (CH340G).
- Two DC motor outputs (L9110S dual H-bridge, 800 mA each), `motor_1` and `motor_2`.
- One WS2812B RGB LED on `board.NEOPIXEL` (IO2).
- STEMMA QT / QWIIC connector for I2C modules, plus `SDA`/`SCL` headers.
- Every header pin has its own GND and V+ pin beside it.
- Power: USB, or 5 to 9 V DC on the Vin screw terminal.
- **Jumper**: SELECT-to-Vin sends the Vin voltage to the V+ rail and the motors;
  SELECT-to-+3.3V sends 3.3 V instead. The blue 3.3 V pins are always 3.3 V. Removing the
  jumper disables the motors and the V+ rail.
- **BOOT button** on IO0 (reads LOW when pressed). **RESET button** restarts the board.

## 2. How code runs

- The board appears as a USB drive named `CIRCUITPY`. `code.py` in its root runs
  automatically at power-on and after every save. Libraries live in `CIRCUITPY/lib/`.
- Students normally use **IdeaCode** (https://ideacode.crcibernetica.com, Chrome/Edge):
  Connect, edit, Ctrl+R runs the editor content as `code.py`. Output from `print()`
  appears in the console. Ctrl+C stops the program. Thonny works the same way.
- CircuitPython version is 10.x. Use f-strings freely.
- There is no `input()` from a user in a robot. Use buttons, sensors, or timing.
- A program that ends stops everything. Almost every program needs `while True:` with a
  `time.sleep()` inside it. Sleeps of 0.01 to 0.1 s are typical.

## 3. Pin map

Use `board.IOnn` names, e.g. `board.IO27`. These are the header pins:

| Pin | Capabilities | Notes |
|---|---|---|
| IO4 | digital, PWM, analog in*, touch | |
| IO5 | digital, PWM, SPI CS | |
| IO18 | digital, PWM, SPI CLK | |
| IO19 | digital, PWM, SPI MISO | |
| IO21 | I2C SDA | reserved for I2C |
| IO22 | I2C SCL | reserved for I2C |
| IO23 | digital, PWM, SPI MOSI | |
| IO25 | digital, PWM, analog in*, **DAC** | |
| IO26 | digital, PWM, analog in*, **DAC** | |
| IO27 | digital, PWM, analog in*, touch | |
| IO32 | digital, PWM, analog in, touch | |
| IO33 | digital, PWM, analog in, touch | |
| IO34 | analog in, digital **input only** | no internal pull-up/down |
| IO35 | analog in, digital **input only** | no internal pull-up/down |
| IO36 | analog in, digital **input only** | no internal pull-up/down |
| IO39 | analog in, digital **input only** | no internal pull-up/down |
| IO0 | BOOT button | usable as a button input, LOW = pressed |

\* IO4, IO25, IO26 and IO27 **cannot be analog inputs while Wi-Fi is in use**. For
analog sensors prefer IO32, IO33, IO34, IO35, IO36, IO39.

Pins **not available** to the student: IO12, IO13, IO14, IO15 (motor driver), IO2 (RGB
LED), TX0/RX0 (USB serial). `IdeaBoard()` claims the motor pins and the LED when created.

Good defaults when the student does not specify a pin: servo on IO4, digital output or
buzzer on IO27, digital input (button) on IO33 with pull-up, analog input on IO33 or
IO32, second servo on IO5, ultrasonic trigger/echo on IO18/IO19.

## 4. The `ideaboard` library

Always start with:

```python
import time
import board
from ideaboard import IdeaBoard

ib = IdeaBoard()
```

### Motors

```python
ib.motor_1.throttle = 1.0    # full forward
ib.motor_2.throttle = -0.5   # half speed reverse
ib.motor_1.throttle = 0      # brake
ib.motor_1.throttle = None   # coast (roll freely)
```

Range is -1.0 to 1.0. Motor direction depends on wiring, so define the robot's motions
as small functions (`forward()`, `backward()`, `turn_left()`, `turn_right()`, `stop()`)
and tell the student to swap a sign if a wheel turns the wrong way. Small robots often
need at least 0.4 to 0.5 to move at all.

### RGB LED

```python
ib.brightness = 0.2          # 0.0 to 1.0, default 0.3
ib.pixel = (255, 0, 0)       # (red, green, blue), each 0 to 255
ib.pixel = (0, 0, 0)         # off
ib.arcoiris = 128            # colour wheel position 0 to 255 (arcoiris = rainbow)
color = ib.pixel             # read back the current (r, g, b)
```

### Servo

```python
servo = ib.Servo(board.IO4)  # any PWM pin; optional freq=50, min_pulse=500, max_pulse=2500
servo.angle = 90             # 0 to 180 degrees
```

Servos take about 0.5 s to travel the full range; add `time.sleep()` after a move.
Continuous-rotation servos use `angle` around 90 as stop, below for one direction,
above for the other.

### Digital in / out

```python
button = ib.DigitalIn(board.IO33, pull=ib.UP)   # pull can be ib.UP, ib.DOWN or None
if not button.value:                             # with pull-up, pressed reads False
    ...

led = ib.DigitalOut(board.IO27)
led.value = True
```

Wire a button between the pin and GND and use `pull=ib.UP`. Input-only pins (34, 35,
36, 39) have no internal pull resistors, so use an external one or choose another pin.

### Analog in

```python
sensor = ib.AnalogIn(board.IO33)
raw = sensor.value                  # 0 to 65535 for 0 to 3.3 V
volts = raw * 3.3 / 65535
```

### Analog out (DAC)

```python
dac = ib.AnalogOut(board.IO26)      # only IO25 or IO26
dac.value = 32768                   # 0 to 65535 -> 0 to 3.3 V
```

`dac.value` is write-only in this library; reading it raises an error.

### map_range

```python
angle = ib.map_range(raw, 0, 65535, 0, 180)   # scales and clamps, returns a float
```

## 5. Plain CircuitPython the student will also need

### The BOOT button as a start button

```python
import keypad
keys = keypad.Keys((board.IO0,), value_when_pressed=False)

while True:
    event = keys.events.get()
    if event and event.pressed:
        print("start")
```

`keypad` debounces and queues presses, so it is better than polling for any button.
Extra buttons on other pins can be added to the same tuple with `pull=True` (default).

### Capacitive touch

```python
import touchio
touch = touchio.TouchIn(board.IO4)    # touch pins: IO4, IO27, IO32, IO33
if touch.value: ...
```

### Buzzer and music

A passive buzzer between a pin (IO27 is typical) and GND. Simple tones:

```python
import pwmio
buzzer = pwmio.PWMOut(board.IO27, variable_frequency=True)
buzzer.frequency = 440
buzzer.duty_cycle = 2 ** 15     # 50 % = sound on
time.sleep(0.5)
buzzer.duty_cycle = 0           # off
```

Tunes use RTTTL strings with `adafruit_rtttl` (installed in `lib/`, together with its
dependency `adafruit_waveform`). Thousands of songs exist online; search "RTTTL songs":

```python
from adafruit_rtttl import play
play(board.IO27, "IronMan:d=4,o=5,b=155:2b4,2d5,4d5,4e5,2e5,8g5,8f#5,8g5,8f#5,8g5,8f#5,4d5,4d5,4e5,2e5")
```

### Ultrasonic distance (HC-SR04)

`adafruit_hcsr04` is not installed by default; if the student has it:

```python
import adafruit_hcsr04
sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.IO18, echo_pin=board.IO19)
try:
    print(sonar.distance)   # cm
except RuntimeError:
    pass                    # no echo this time; ignore and retry
```

### I2C devices

```python
i2c = board.I2C()           # SDA = IO21, SCL = IO22, also the STEMMA QT connector
```

To find an address, scan the bus:

```python
while not i2c.try_lock():
    pass
print([hex(a) for a in i2c.scan()])
i2c.unlock()
```

Adafruit I2C drivers (`.mpy` files) must be copied to `lib/`. Installed by default:
`adafruit_lsm6ds` (accelerometer/gyro), `adafruit_sht31d` (temperature/humidity),
`adafruit_ltr329_ltr303` (light), `adafruit_ht16k33` (LED matrix), `adafruit_register`,
`adafruit_motor`, `neopixel`, `simpleio`, `adafruit_requests`, `adafruit_minimqtt`,
`adafruit_io`, `adafruit_ticks`, `adafruit_rtttl`, `adafruit_waveform`, plus `ideaboard`,
`ideasense`, `sumobotv2`, `font5x5`.

### Wi-Fi and HTTP

Credentials go in a separate `secrets.py` on the board:

```python
secrets = {"ssid": "MyWifi", "password": "mypassword"}
```

```python
import wifi, socketpool, ssl
import adafruit_requests
from secrets import secrets

wifi.radio.connect(secrets["ssid"], secrets["password"])
print("IP:", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
data = requests.get("http://api.open-notify.org/iss-now.json").json()
```

Adafruit IO (MQTT dashboards) works with `adafruit_minimqtt` and `adafruit_io`; the
`examples/adafruit_io_test.py` file in this repository is the working template.
Remember analog pins IO4/25/26/27 stop working while Wi-Fi is on.

### ESP-NOW (board-to-board radio, no router)

```python
import espnow
e = espnow.ESPNow()
e.peers.append(espnow.Peer(mac=b'\xd4\xd4\xda\x16\xb7\x1c'))   # receiver's MAC
e.send("hello")
```

Receiver: `if e: packet = e.read(); print(packet.msg)`. A board's MAC is
`wifi.radio.mac_address`. Handy for a remote control made from two IdeaBoards.

### Extra LEDs and strips

```python
import neopixel
strip = neopixel.NeoPixel(board.IO27, 8, brightness=0.2)   # 8 pixels on IO27
strip[0] = (0, 255, 0)
strip.fill((0, 0, 50))
```

## 6. Rules for generated code

1. Create `ib = IdeaBoard()` once, at the top. Never create it twice and never use
   `pwmio`/`digitalio` directly on IO2, IO12 to IO15.
2. Do not use `board.LED`, `board.D13`, `board.A0`, `machine`, `RPi.GPIO`, `pyserial`,
   `numpy`, threads, or `asyncio` unless the student asks. This is CircuitPython, not
   MicroPython or desktop Python.
3. Every loop must sleep. A `while True:` without `time.sleep()` starves the USB
   console and makes the board hard to stop.
4. Use `time.monotonic()` for timing several things at once instead of long sleeps.
5. Stop the motors (`throttle = 0`) before the program ends and in any error handler.
6. Prefer the `ideaboard` helpers over raw `digitalio`/`analogio`/`pwmio` for pins;
   drop to raw modules only for things the library does not cover.
7. Mention which physical pins to wire and that sensors share GND with the board.
8. Values: analog 0 to 65535, servo 0 to 180, throttle -1.0 to 1.0, colours 0 to 255.
9. When a library is not installed by default, say so and name the `.mpy` file to copy
   from the Adafruit CircuitPython Bundle into `CIRCUITPY/lib/`.
10. Give a complete program, not a fragment, unless the student asks for a change to
    code they pasted. Keep it under about 80 lines when possible.

## 7. Program skeleton

```python
import time
import board
import keypad
from ideaboard import IdeaBoard

ib = IdeaBoard()
keys = keypad.Keys((board.IO0,), value_when_pressed=False)   # BOOT button

def stop():
    ib.motor_1.throttle = 0
    ib.motor_2.throttle = 0

ib.pixel = (0, 0, 255)          # blue = waiting
print("Press BOOT to start")
while True:
    event = keys.events.get()
    if event and event.pressed:
        break
    time.sleep(0.01)

ib.pixel = (0, 255, 0)          # green = running
try:
    while True:
        # main behaviour here
        time.sleep(0.05)
finally:
    stop()
    ib.pixel = (0, 0, 0)
```

## 8. Examples in this repository

`examples/`: `blink.py`, `pixel.py`, `arcoiris.py`, `motors.py`, `servo_simple.py`,
`digitalin.py`, `digitalout.py`, `analogin.py`, `analogout.py`, `map_range.py`,
`wifi_simple.py`, `adafruit_io_test.py`, `secrets.py`.

Full documentation: https://github.com/CRCibernetica/circuitpython-ideaboard/wiki
