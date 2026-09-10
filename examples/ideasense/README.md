# IdeaSense Library

The `IdeaSense` library provides a streamlined, unified Python interface for the IdeaSense hardware board. It automatically initializes the I2C bus and abstracts the complexity of interacting with the onboard sensors, buttons, and LED matrix into a single, easy-to-use Python class.

## Supported Hardware Features

The `IdeaSense` class acts as a wrapper for the following hardware components:

* **LED Matrix**: A 5x5 LED matrix powered by the HT16K33 chip. The library includes a custom wrapper that corrects hardware orientation and coordinate offsets so you can interact with it using a standard `(x, y)` grid ranging from 0 to 4.
* **Temperature & Humidity**: Reads ambient data using the SHT31D sensor.
* **Light Sensing**: Reads visible plus infrared (IR) light using the LTR303 sensor.
* **Motion Tracking**: Captures acceleration and gyroscope data using the LSM6DS3TRC 6-axis IMU.
* **User Inputs**: Reads the state of 3 onboard buttons mapped via the matrix I2C device. The library exposes a keypad-style event queue (`idea.events.get()`) as well as `pressed` / `released` / `held` properties. Hardware polling happens automatically when any of these are accessed.

## Dependencies

To use this library, ensure you have the appropriate Adafruit CircuitPython/Blinka libraries installed for the underlying hardware:

* `adafruit_sht31d`
* `adafruit_ltr329_ltr303`
* `adafruit_lsm6ds`
* `adafruit_ht16k33`

## Quick Start & API Reference

### Initialization

To start interacting with the board, simply instantiate the `IdeaSense` class. This automatically sets up the I2C connection.

```python
from ideasense import IdeaSense

idea = IdeaSense()

```

### Display / Matrix Operations

The matrix is accessible via the `idea.matrix` property. It accepts coordinates between `0` and `4`.

```python
# Clear the screen
idea.matrix.fill(0) 

# Turn on the top-left pixel
idea.matrix[0, 0] = 1 

# Turn on the bottom-right pixel
idea.matrix[4, 4] = 1 

# Adjust brightness (0.0 to 1.0)
idea.matrix.brightness(0.5)

# Push your changes to the physical display
idea.matrix.show()

```

### Reading Sensors

Sensor properties return raw data directly from the hardware.

```python
# Environment
temperature = idea.temp      # Returns temperature in Celsius
humidity = idea.humid        # Returns relative humidity percentage
light_level = idea.light     # Returns visible + IR light levels

# Motion
accel_x, accel_y, accel_z = idea.accel  # Returns acceleration tuple
gyro_x, gyro_y, gyro_z = idea.gyro      # Returns gyroscope tuple

```

### Button Inputs

The library polls the button hardware automatically whenever you access the button API — just read the events or properties below and polling happens for you.

There are two ways to read the three onboard buttons:

**1. Event queue (keypad-style).** `idea.events.get()` returns the next press/release event, or `None` when the queue is empty. Each event has `.key_number` (0, 1, 2), `.pressed` (`True` for press, `False` for release), and `.timestamp`.

```python
from ideasense import IdeaSense
import time

idea = IdeaSense()
names = ("A", "B", "C")

while True:
    time.sleep(0.01)
    event = idea.events.get()
    if event:
        action = "pressed" if event.pressed else "released"
        print(f"Button {names[event.key_number]} {action}")
```

**2. State properties.** Each returns a list `[Button_A, Button_B, Button_C]`:

* **`idea.pressed`**: `True` for one tick on the exact moment a button transitions from up to down.
* **`idea.released`**: `True` for one tick on the exact moment a button transitions from down to up.
* **`idea.held`**: `True` while a button is currently being held down.

```python
from ideasense import IdeaSense
import time

idea = IdeaSense()

while True:
    # Fires once per push
    if idea.pressed[0]:
        print("Button A was just pressed!")

    # True every tick while held
    if idea.held[2]:
        print("Button C is being held")

    time.sleep(0.05)
```

## Included Examples

This repository includes several example scripts to help you get started:

* `ideasense_simpletest.py`: A basic diagnostic script that tests the matrix, prints all sensor readings, and detects button presses.
* `button_test.py`: A minimal keypad-style example showing press/release events for all three buttons.
* `button_demo.py`: A fully annotated walkthrough of every button API — event queue, `pressed`, `released`, and `held` — in a single loop.
* `text_demo.py` & `font5x5.py`: Demonstrates how to use an external font dictionary to scroll alphanumeric characters across the 5x5 matrix smoothly.
* `weather_station.py`: An interactive application that maps buttons to scroll the current temperature or humidity across the display.
* `sand.py`: A fun physics toy that uses the accelerometer to simulate grains of sand falling across the 5x5 matrix based on how you tilt the board.
