# IdeaBoard: adding a sensor or library that is not installed

You are helping a student use a sensor, display, or other peripheral on the
**CRCibernetica IdeaBoard** that the `ideaboard.md` reference does not cover. Read
`ideaboard.md` first for the pin map and the code rules; this document explains how to
find the right CircuitPython library, get it onto the board, and prove it works.

Never guess a library name, a class name, or an I2C address. Look them up with the steps
below and tell the student exactly which files you found and where they came from.

## 1. Facts about this board that change the usual advice

- The IdeaBoard is an original ESP32 behind a CH340 USB-serial chip. It **never appears
  as a USB drive**. There is no `CIRCUITPY` folder to drag files into.
- **`circup` does not work** with this board. It needs a mounted drive or the Wi-Fi web
  workflow, and neither is available. Do not suggest it.
- Everything goes through the serial REPL. The student's tools are **IdeaCode**
  (https://ideacode.crcibernetica.com, Chrome/Edge) and **Thonny**. An AI agent with a
  shell can use `tools/ibserial.py` from this repository (section 5).
- Only one program can hold the serial port at a time. If a tool cannot connect, the
  first thing to check is whether IdeaCode, Thonny, or another terminal is already open.
- CircuitPython is **10.x** (10.1.4 at the time of writing). Library files must come from
  the **10.x** bundles. A `.mpy` from another major version fails with
  `ValueError: incompatible .mpy file`.
- I2C is `board.I2C()` with SDA on IO21 and SCL on IO22, also on the STEMMA QT
  connector. This board has **no `board.STEMMA_I2C()`**; change that line when copying
  Adafruit examples. SPI is `board.SPI()` with SCK IO18, MISO IO19, MOSI IO23.

## 2. Check what is already there before adding anything

Built into the firmware (no file needed, `import` just works):
`adafruit_bus_device`, `adafruit_connection_manager`, `adafruit_motor`,
`adafruit_pixelbuf`, `adafruit_requests`, `neopixel`, `simpleio`, `ulab` (numpy-like),
plus all the core modules: `analogio`, `audiobusio`, `audiocore`, `audiomixer`,
`audiomp3`, `bitbangio`, `busio`, `countio`, `digitalio`, `displayio`, `espnow`,
`frequencyio`, `i2cdisplaybus`, `keypad`, `onewireio`, `pulseio`, `pwmio`, `rotaryio`,
`sdcardio`, `socketpool`, `ssl`, `touchio`, `wifi`, and more (`help("modules")` at the
REPL prints the full list).

Shipped in `lib/` by this repository: `adafruit_ds18x20`,
`adafruit_ht16k33`, `adafruit_io`, `adafruit_lsm6ds`, `adafruit_ltr329_ltr303`,
`adafruit_minimqtt`, `adafruit_msa3xx`, `adafruit_onewire`, `adafruit_register`,
`adafruit_rtttl`, `adafruit_sht31d`, `adafruit_ticks`, `adafruit_waveform`,
`font5x5`, `hcsr04` (ultrasonic, see ideaboard.md), `ideaboard`, `ideasense`, `sumobotv2`. A student's board may have more or
fewer; when in doubt ask them to look in **Device > lib** in IdeaCode, or run
`tools/ibserial.py ls /lib`.

If the peripheral is covered by one of these, use it and stop here.

## 3. Find the library

Adafruit documents every library in the bundle at **docs.circuitpython.org**.

1. **Catalogue page** (one page, all ~800 Adafruit libraries, grouped by category:
   Motion Sensors, Environmental Sensors, Light Sensors, Distance Sensors, Displays,
   Real-time clocks, IO Expansion, Radio, LED and motor helpers, ...):
   `https://docs.circuitpython.org/projects/bundle/en/latest/drivers.html`
   Each entry reads like `BME280 Temperature, Humidity and Pressure (adafruit_bme280)`,
   so search it for the chip number (BME280, VL53L0X, PCA9685, SSD1306, ...) or, if the
   student only knows the sensor type, for words such as "distance" or "CO2".
2. **Per-library pages**, where `<name>` is the module name without the `adafruit_`
   prefix (`adafruit_bme280` -> `bme280`):
   - `https://docs.circuitpython.org/projects/<name>/en/latest/` : introduction,
     **dependencies**, a short usage snippet.
   - `https://docs.circuitpython.org/projects/<name>/en/latest/examples.html` : the full
     `*_simpletest.py`. Start from this, not from memory.
   - `https://docs.circuitpython.org/projects/<name>/en/latest/api.html` : classes,
     properties, constructor arguments (including `address=`).
3. **Wiring and I2C address** are not on those pages. They are in the Adafruit Learn
   guide linked from the introduction page, on the breakout's product page, or in the
   chip datasheet. Many chips have two possible addresses selected by a solder jumper or
   an `SDO`/`ADDR` pin; the simpletest often shows the alternative in a comment.
4. **Community bundle** (libraries by other authors, about 180 of them): the lists live in
   the `adafruit/CircuitPython_Community_Bundle` repository on GitHub, files
   `circuitpython_community_library_list.md` and
   `circuitpython_community_auto_library_list.md`. Each links to the library's own repo,
   which has the README and `examples/`.
5. If neither bundle has it, search GitHub for `circuitpython <chip>`. Check the result
   targets CircuitPython (uses `busio`/`board`), not MicroPython (uses `machine`).

## 4. Get the files

- Download the **Bundle for Version 10.x** (`adafruit-circuitpython-bundle-10.x-mpy-<date>.zip`)
  from https://circuitpython.org/libraries, and the **Community Bundle for 10.x** from the
  same page if needed. Unzip it once; keep it.
- Inside the zip, `lib/` holds every library, either as one file (`adafruit_bme680.mpy`)
  or as a folder (`adafruit_bme280/`). Copy the whole folder when it is a folder.
- **Dependencies**: the introduction page lists them, and so does
  `requirements/<library>/requirements.txt` inside the bundle. Ignore `Adafruit-Blinka`
  (desktop only) and anything in the built-in list from section 2. What is left must
  also be copied to `/lib`. `adafruit_register` is the most common one and is already
  shipped.
- Prefer `.mpy` over `.py` on this board: they load faster and use much less RAM.
- Tell the student the exact file or folder names, for example:
  "copy `lib/adafruit_vl53l0x.mpy` from the 10.x bundle into `/lib` on the board".

## 5. Put the files on the board

Three ways. All end with the file inside `/lib` on the board.

**IdeaCode** (student, browser): Connect, open **Device > lib** in the file tree,
right-click `lib` and upload the `.mpy` file, or drag it from the Local panel to the
Device panel. Folders: create the folder under `lib` first, then upload the files into
it (`__init__.py` included, even when it is empty).

**Thonny** (student, desktop): View > Files, open `lib` in the device pane (bottom),
navigate to the file or folder in the computer pane (top), right-click > *Upload to /lib*.
Thonny uploads folders whole.

**Agent with a shell** (you, if you can run commands on the student's computer):
`tools/ibserial.py` in this repository needs only Python 3 and `pyserial`. It finds the
CH340 port itself on Linux, macOS, and Windows, or take `--port` / `IBSERIAL_PORT`.

```
uv run tools/ibserial.py info                        # version, free flash, /lib listing
uv run tools/ibserial.py scan                        # I2C addresses currently on the bus
uv run tools/ibserial.py put bundle/lib/adafruit_bme280 /lib/adafruit_bme280
uv run tools/ibserial.py put bundle/lib/adafruit_vl53l0x.mpy /lib/adafruit_vl53l0x.mpy
uv run tools/ibserial.py exec "import adafruit_bme280.basic; print('ok')"
uv run tools/ibserial.py run test_sensor.py          # run a local script, stream output, Ctrl-C stops
uv run tools/ibserial.py put main_program.py /code.py && uv run tools/ibserial.py reset
uv run tools/ibserial.py rm /lib/adafruit_bme280     # undo
```

(`pip install pyserial` then `python tools/ibserial.py ...` works the same.) The script
stops `code.py` while it works; `reset` starts it again. Close IdeaCode or Thonny first,
and tell the student to reconnect their tool afterwards.

## 6. Prove it works, in this order

1. **Scan the bus** and compare with the expected address. No device found means wiring
   or power, not software: check SDA/SCL are not swapped, GND is shared, the module is
   3.3 V compatible, and it is not on an analog-only pin.
   ```python
   import board
   i2c = board.I2C()
   while not i2c.try_lock():
       pass
   print([hex(a) for a in i2c.scan()])
   i2c.unlock()
   ```
2. **Import** the module on its own. `ImportError: no module named ...` means the file is
   not in `/lib`, or the folder is missing `__init__.py`, or a dependency is absent.
3. **Run the simpletest** adapted to this board: `board.I2C()` instead of
   `board.STEMMA_I2C()`, IdeaBoard pin names (`board.IO27`, not `board.D5`), and the
   address from step 1 if it differs from the default (`address=0x77`).
4. Only then merge it into the student's program, keeping the rules from `ideaboard.md`
   (one `IdeaBoard()` object, a sleep in every loop, motors stopped in `finally:`).

## 7. When no library exists

Say so plainly, then offer the smallest path that works:

- A **MicroPython** driver for the same chip can usually be ported: replace
  `machine.I2C` with `busio.I2C`/`board.I2C()` and use `adafruit_bus_device.i2c_device`
  for transfers. Keep the register addresses and the maths; that is the hard part and it
  is already done.
- Otherwise write a minimal driver from the datasheet's register map. Built-in
  `adafruit_bus_device` handles locking and addressing:

  ```python
  import struct
  import board
  from adafruit_bus_device.i2c_device import I2CDevice

  class MySensor:
      def __init__(self, i2c, address=0x48):
          self.dev = I2CDevice(i2c, address)

      def _read(self, reg, n):
          buf = bytearray(n)
          with self.dev:
              self.dev.write_then_readinto(bytes([reg]), buf)
          return buf

      @property
      def temperature(self):
          raw = struct.unpack(">h", self._read(0x00, 2))[0]
          return raw / 256          # scale from the datasheet
  ```

  Save it as `/lib/mysensor.py`. Read one register first and print the raw bytes before
  writing any conversion maths.
- Analog sensors (LDR, potentiometer, soil moisture, MQ gas modules) need no library at
  all: `ib.AnalogIn(board.IO33)`. Simple digital modules (PIR, tilt, line sensor with a
  digital output) are `ib.DigitalIn`.

## 8. Common errors and what they mean

| Message | Cause | Fix |
|---|---|---|
| `ImportError: no module named 'adafruit_x'` | file not in `/lib`, wrong name, or missing `__init__.py` | check `ls /lib`; copy the folder, not just one file inside it |
| `ValueError: incompatible .mpy file` | `.mpy` from a 9.x or older bundle | use the 10.x bundle |
| `ValueError: No I2C device at address: 0x77` | wiring, power, or the other address | scan; pass `address=` |
| `OSError: [Errno 19] ENODEV` / `[Errno 5] EIO` | device stopped answering mid-transfer | loose wire, too-long cable, or missing pull-ups |
| `MemoryError` | too many large `.py` files imported | use `.mpy`; import fewer modules; `gc.collect()` |
| `RuntimeError: ... in use` | pin already claimed | `IdeaBoard()` owns IO2, IO12 to IO15; SDA/SCL are I2C only |
| Tool cannot open the port | another program is connected | close IdeaCode/Thonny; on Linux check the `uucp`/`dialout` group |
| `ValueError: ... not a valid pin` | pin name from another board | use `board.IOnn` names from the pin map |

## 9. Rules for your answer

1. Name the library exactly as it appears on the drivers page, and give the
   docs.circuitpython.org URL you used.
2. List every file or folder to copy, dependencies included, and say which bundle.
3. Give the install steps for the tool the student uses (IdeaCode unless they say
   otherwise). Never mention `circup` or a `CIRCUITPY` drive.
4. Give the scan-then-import-then-simpletest sequence before the final program.
5. Adapt the example to IdeaBoard pin names and `board.I2C()`.
6. If you cannot verify that a library exists, say that you could not, and fall back to
   section 7 rather than inventing an API.
