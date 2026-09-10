# SumoBot v2 Library
#
# Snapshot of ch32v003/sumobotv2/examples/sumobotv2.py (commit 5b4b3ec).
# The ch32v003 repo is the source of truth for this library and the sensor
# board firmware; update this copy from there rather than editing it here.
# Requires lib/adafruit_lsm6ds and lib/adafruit_register.
#
# The board carries two sensor devices on one shared I2C bus:
#   * an LSM6DS3TR-C IMU (accelerometer + gyroscope) at address 0x6B
#   * a CH32V003 analog sensor front-end at address 0x34, providing five
#     analog channels plus a reflective RGB color sensor
#
# Usage:
#     from sumobotv2 import SumoBotV2
#     sumo = SumoBotV2()
#
#     ax, ay, az = sumo.accel
#     gx, gy, gz = sumo.gyro
#     s1, s2, s3, s4 = sumo.infrared
#     sumo.led = (255, 0, 0)            # the LED is yours as an indicator
#
#     r, g, b = sumo.color()            # measure the surface colour
#
# The board powers up with the LED off, so the IR sensors and the LED-as-indicator
# work straight away. Color sensing happens only when you ask: color() runs one
# measurement, about 25 ms, and gives the LED straight back.
#
# --- About the color sensor ---
# A single WS2812B shines red, then green, then blue at the surface,
# and one light detector measures how much of each bunces back.
# A red surface reflects red strongly and green/blue weakly, and
# that difference is what identifies the colour.
#
# A fourth "dark" reading is taken with the LED off. color() turns those four
# numbers into a color in two steps:
#
#     1. subtract dark from each channel   -- removes room lighting
#     2. divide each by their total        -- removes how MUCH light there is,
#                                             which changes with sensor height
#
# What is left is the proportions, and the proportions are the color. Move the
# sensor closer and the raw counts all grow, but color() stays put.

import time

import board
from adafruit_lsm6ds.lsm6ds3trc import LSM6DS3TRC

# --- Sensor board (CH32V003 I2C slave) ---------------------------------------
_ADDR = 0x34             # 7-bit I2C address of the sensor front-end

_REG_ANALOG = 0x00       # S1 low byte; 10 bytes cover all five channels
_REG_WHO_AM_I = 0x10     # device id register
_REG_VERSION = 0x11      # firmware revision
_REG_COLOR = 0x20        # colour block: dark, red, green, blue, counter
_REG_COLOR_COUNT = 0x28  # just the sample counter, to see if a measurement is new
_REG_MODE = 0x30         # 1 = manual LED, 2 = measure once
_REG_ILLUMINATION = 0x34  # LED level used during a measurement

_WHO_AM_I = 0x34         # expected id value
_MIN_FIRMWARE = 0x08     # oldest revision this library speaks to

_MODE_MANUAL = 1         # we drive the LED directly
_MODE_MEASURE = 2        # firmware measures once, then reverts to _MODE_MANUAL

# How long a measurement takes on the board: four 5 ms settles plus the LED
# frames, conversions and a little slack. A measurement waits this out rather
# than polling, so it wants to be generous but not wasteful.
#
# This tracks COLOR_SETTLE_MS in the firmware. If that changes, change this --
# the board does not publish its measurement duration.
_MEASURE_WAIT = 0.030


class SensorBoard:
    """Driver for the CH32V003 analog + colour sensor front-end.

    Each analog channel is a 10-bit value (0..1023) held as two little-endian
    bytes. Channels are burst-read in one transaction so the frame is always
    self-consistent (see the board DATASHEET, section 10.5).
    """

    def __init__(self, i2c, address=_ADDR):
        self._i2c = i2c
        self._addr = address
        self._analog_buf = bytearray(10)
        self._color_buf = bytearray(9)
        self._count_buf = bytearray(1)

        who = self.who_am_i
        if who != _WHO_AM_I:
            raise RuntimeError(
                "SumoBot v2 sensor board not found at 0x%02X "
                "(WHO_AM_I=0x%02X, expected 0x%02X)"
                % (self._addr, who, _WHO_AM_I)
            )

        # Checked once here rather than per-call. Older revisions differ in ways
        # this library does not paper over: 0x03 and earlier could tear the colour
        # block mid-read, and 0x07 and earlier had a continuous colour mode that
        # no longer exists.
        self.firmware = self._read(_REG_VERSION, bytearray(1))[0]
        if self.firmware < _MIN_FIRMWARE:
            raise RuntimeError(
                "sensor board firmware 0x%02X is too old for this library "
                "(needs 0x%02X or later)" % (self.firmware, _MIN_FIRMWARE)
            )

    # --- low-level I2C ------------------------------------------------------
    def _read(self, reg, buf):
        """Set the read pointer to reg, then fill buf in one transaction."""
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto_then_readfrom(self._addr, bytes([reg]), buf)
        finally:
            self._i2c.unlock()
        return buf

    def _write(self, reg, values):
        """Write one or more bytes starting at reg."""
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto(self._addr, bytes([reg]) + bytes(values))
        finally:
            self._i2c.unlock()

    # --- identification -----------------------------------------------------
    @property
    def who_am_i(self):
        return self._read(_REG_WHO_AM_I, bytearray(1))[0]

    # --- analog channels ----------------------------------------------------
    @property
    def analog(self):
        """All five analog channels as 10-bit ints: [s1, s2, s3, s4, s5].

        The board converts all five inside this transaction, before it answers,
        so these are readings taken microseconds ago. Reading all five at once
        also means they come from the same instant, which separate reads would
        not give you.
        """
        buf = self._read(_REG_ANALOG, self._analog_buf)
        return [buf[2 * i] | (buf[2 * i + 1] << 8) for i in range(5)]

    @property
    def infrared(self):
        """The four IR reflectance channels: [s1, s2, s3, s4]."""
        return self.analog[:4]

    @property
    def detector(self):
        """Sensor 5, the colour detector, as a plain light-level reading.

        Steady, because nothing drives the LED but you: set it, wait a few
        milliseconds for the detector to settle, and read. The board applies an
        LED write in microseconds and converts the detector inside this read, so
        5 ms is enough.

        For a colour, use color() -- it does exactly this four times over with
        the settle timing owned by the board rather than by your sleeps.
        """
        return self.analog[4]

    # --- colour -------------------------------------------------------------
    def _measure(self, timeout):
        """Trigger one measurement and return (dark, red, green, blue, count)."""
        before = self._read(_REG_COLOR_COUNT, self._count_buf)[0]
        self._write(_REG_MODE, [_MODE_MEASURE])

        # Wait the measurement out, then confirm the counter moved. The counter
        # is the only evidence that matters -- it says "this frame is a new one".
        #
        # Deliberately NOT a tight poll. An earlier version read the mode register
        # every 2 ms waiting for the board to clear it, and that never completed
        # even though the board demonstrably finished in ~20 ms and published
        # correctly. The cause was never pinned down; hammering the bus while the
        # board is measuring is the obvious suspect. Waiting and then checking is
        # what was shown to work by hand, and it leaves the bus alone.
        #
        # monotonic_ns() rather than monotonic(): the latter is a float in
        # CircuitPython and loses resolution as uptime grows, which is a poor
        # basis for a sub-second deadline.
        deadline = time.monotonic_ns() + int(timeout * 1e9)
        while True:
            time.sleep(_MEASURE_WAIT)
            frame = self.last_color_frame
            if frame[4] != before:
                return frame
            if time.monotonic_ns() > deadline:
                raise RuntimeError(
                    "colour measurement did not complete in %.3f s "
                    "(counter stuck at %d)" % (timeout, before)
                )

    def color(self, timeout=0.5):
        """Measure the surface colour: (r, g, b), each 0.0 to 1.0, summing to 1.

        Dark-corrected and normalized -- see the notes at the top of this file.
        This is the number to compare against stored references; it stays put as
        the sensor's height above the surface changes, where raw counts do not.

        Takes about 25 ms. The LED is borrowed for that long and then put back to
        whatever colour you had set.

        Returns (0.0, 0.0, 0.0) if there is no reflected light at all -- a black
        surface, no surface, or the illumination turned off.
        """
        dark, red, green, blue, _ = self._measure(timeout)

        r = max(0, red - dark)
        g = max(0, green - dark)
        b = max(0, blue - dark)
        total = r + g + b
        if not total:
            return (0.0, 0.0, 0.0)
        return (r / total, g / total, b / total)

    def raw_color(self, timeout=0.5):
        """Measure and return the uncorrected counts: (dark, red, green, blue).

        The same measurement color() uses, before dark subtraction and
        normalizing. Use it to check for clipping -- any channel near 1023 means
        the ADC saturated and the reading is wrong -- or to do the arithmetic
        yourself.
        """
        dark, red, green, blue, _ = self._measure(timeout)
        return (dark, red, green, blue)

    @property
    def last_color_frame(self):
        """(dark, red, green, blue, count) from the last measurement, no new one.

        Reads the published block without asking the board to measure. `count`
        advances by one per measurement and wraps at 255. Mostly of interest to
        diagnostics; color() and raw_color() are what you normally want.

        One plain burst read is enough. The board publishes this block from its
        I2C interrupt on the STOP event -- between transactions -- so it cannot
        change underneath a read, and all five values come from one measurement.
        """
        buf = self._read(_REG_COLOR, self._color_buf)
        return (
            buf[0] | (buf[1] << 8),
            buf[2] | (buf[3] << 8),
            buf[4] | (buf[5] << 8),
            buf[6] | (buf[7] << 8),
            buf[8],
        )

    # --- LED ----------------------------------------------------------------
    @property
    def led(self):
        """The indicator colour as (red, green, blue)."""
        buf = self._read(_REG_MODE, bytearray(4))
        return (buf[1], buf[2], buf[3])

    @led.setter
    def led(self, rgb):
        """Use the LED as a plain indicator: sumo.led = (255, 0, 0).

        The LED is yours except during a measurement, which borrows it for ~25 ms
        and then puts this colour back. The board pushes a new colour out within
        microseconds of this write.
        """
        red, green, blue = rgb
        self._write(
            _REG_MODE,
            [
                _MODE_MANUAL,
                max(0, min(255, int(red))),
                max(0, min(255, int(green))),
                max(0, min(255, int(blue))),
            ],
        )

    @property
    def illumination(self):
        """LED level used during a measurement (0..255). Not the indicator."""
        return self._read(_REG_ILLUMINATION, bytearray(1))[0]

    @illumination.setter
    def illumination(self, value):
        """Set the measurement LED level (0..255).

        Leave it at 255 unless a channel in raw_color() reads near 1023, which
        means the ADC is clipping and the measurement is wrong.

        Do NOT turn it down casually. There is an unexplained fault on the board
        that makes low levels unreliable: measurements repeat in a four-state
        cycle whose severity depends on the level. At 255 the four states agree
        to within about 1% once normalized. At 127 and 128 they are wildly
        different -- on green tape one of them reads blue-dominant. The obvious
        "half brightness" value is one of the bad ones. See DATASHEET section 7.5.
        """
        self._write(_REG_ILLUMINATION, [max(0, min(255, int(value)))])


# --- SumoBot v2 -------------------------------------------------------------
class SumoBotV2:
    def __init__(self):
        self.i2c = board.I2C()
        self._lsm = LSM6DS3TRC(self.i2c, address=0x6B)
        self.sensor_board = SensorBoard(self.i2c)

    @property
    def firmware(self):
        """Sensor board firmware revision. This library needs 0x08 or later."""
        return self.sensor_board.firmware

    @property
    def accel(self):
        """(x, y, z) acceleration in m/s^2."""
        return self._lsm.acceleration

    @property
    def gyro(self):
        """(x, y, z) angular velocity in rad/s."""
        return self._lsm.gyro

    @property
    def infrared(self):
        """[s1, s2, s3, s4] IR reflectance values (0..1023)."""
        return self.sensor_board.infrared


    @property
    def analog(self):
        """[s1, s2, s3, s4, s5] all five analog channels (0..1023)."""
        return self.sensor_board.analog

    @property
    def detector(self):
        """Sensor 5, the colour detector, as a plain light level (0..1023)."""
        return self.sensor_board.detector

    def color(self, timeout=0.5):
        """Measure the surface colour: (r, g, b) normalized, summing to 1."""
        return self.sensor_board.color(timeout)

    def raw_color(self, timeout=0.5):
        """Measure and return uncorrected counts: (dark, red, green, blue)."""
        return self.sensor_board.raw_color(timeout)

    @property
    def last_color_frame(self):
        """(dark, red, green, blue, count) from the last measurement."""
        return self.sensor_board.last_color_frame

    @property
    def led(self):
        """The indicator colour as (red, green, blue)."""
        return self.sensor_board.led

    @led.setter
    def led(self, rgb):
        """Use the LED as an indicator: sumo.led = (255, 0, 0)."""
        self.sensor_board.led = rgb

    @property
    def illumination(self):
        """LED level used during a measurement (0..255)."""
        return self.sensor_board.illumination

    @illumination.setter
    def illumination(self, value):
        """Set the measurement LED level. Leave it at 255 -- see SensorBoard."""
        self.sensor_board.illumination = value
