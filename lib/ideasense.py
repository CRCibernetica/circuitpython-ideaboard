# IdeaSense Library
#
# CircuitPython helper for the CRCibernetica IdeaSense board: 5x5 LED matrix
# with three buttons (HT16K33 @0x70), SHT30 temperature/humidity (@0x44),
# LTR303 light sensor, and LSM6DS3TR-C accelerometer/gyro (@0x6A).
# Requires lib/adafruit_ht16k33, adafruit_sht31d, adafruit_ltr329_ltr303,
# adafruit_lsm6ds and adafruit_register. API reference: examples/ideasense/README.md

import time
import board
import adafruit_sht31d
import adafruit_ltr329_ltr303 as adafruit_ltr303
from adafruit_lsm6ds.lsm6ds3trc import LSM6DS3TRC
from adafruit_ht16k33 import matrix


class ButtonEvent:
    """A single press or release event. `pressed` is True for press, False for release."""
    def __init__(self, key_number, pressed, timestamp):
        self.key_number = key_number
        self.pressed = pressed
        self.timestamp = timestamp

    def __repr__(self):
        state = "pressed" if self.pressed else "released"
        return f"<ButtonEvent key={self.key_number} {state} t={self.timestamp:.3f}>"


class _EventQueue:
    """Fixed-size FIFO of ButtonEvents. When full, the oldest event is dropped."""
    def __init__(self, parent, maxlen=64):
        self._parent = parent
        self._items = []
        self._maxlen = maxlen

    def _push(self, event):
        if len(self._items) >= self._maxlen:
            self._items.pop(0)
        self._items.append(event)

    def get(self):
        """Return the next event (FIFO), or None if the queue is empty."""
        self._parent._auto_update()
        if self._items:
            return self._items.pop(0)
        return None

    def clear(self):
        self._items = []

    def __len__(self):
        return len(self._items)


class IdeaSense:
    def __init__(self):
        self.i2c = board.I2C()

        # Initialize the raw 8x8 matrix hardware
        self._raw_matrix = matrix.Matrix8x8(self.i2c, address=0x70)
        
        # Wrap the matrix to fix the orientation/offset
        self.matrix = self.MatrixWrapper(self._raw_matrix)
        self.matrix.brightness(0.3)

        self._ltr = adafruit_ltr303.LTR303(self.i2c)
        self._lsm = LSM6DS3TRC(self.i2c, address=0x6a)
        self._sht = adafruit_sht31d.SHT31D(self.i2c, address=0x44)

        # Button state, refreshed by update().
        # The HT16K33 latch clears on read and is only re-set when the keyscan
        # (~10 ms) catches the key down, so polls between scans see 0 even
        # while held. _last_active tracks the last time each bit read as 1, so
        # we can wait _release_timeout before declaring a release.
        self._held = [False, False, False]
        self._pressed = [False, False, False]
        self._released = [False, False, False]
        self._last_active = [0.0, 0.0, 0.0]
        self._release_timeout = 0.15
        self._last_update = 0.0
        self._auto_update_throttle = 0.005
        self.events = _EventQueue(self)

    class MatrixWrapper:
        def __init__(self, raw_matrix):
            self._m = raw_matrix

        def __setitem__(self, key, value):
            """
            Maps (x, y) coordinates to the hardware's actual orientation.
            Based on test feedback:
            - Hardware X requires a +1 offset.
            - X and Y appear swapped/inverted.
            """
            user_x, user_y = key
            
            # Error handling: Restrict x and y to 0-4
            if not (0 <= user_x <= 4 and 0 <= user_y <= 4):
                raise ValueError(f"Matrix coordinates must be between 0 and 4. Received x:{user_x}, y:{user_y}")
            
            # Logic to reorient graph
            hw_x = user_y + 1
            hw_y = user_x
            
            self._m[hw_x, hw_y] = value

        def fill(self, value):
            self._m.fill(value)

        def show(self):
            self._m.show()

        def brightness(self, value):
            self._m.brightness = value

    @property
    def temp(self):
        return self._sht.temperature  

    @property
    def humid(self):
        return self._sht.relative_humidity  

    @property
    def light(self):
        return self._ltr.visible_plus_ir_light  

    @property
    def accel(self):
        return self._lsm.acceleration  

    @property
    def gyro(self):
        return self._lsm.gyro  

    def update(self):
        """Force a poll of the button hardware. Usually called automatically when accessing events/pressed/released/held."""
        key_data = bytearray(6)

        # The [0] is required to access the actual I2CDevice object
        with self._raw_matrix.i2c_device[0] as i2c:
            i2c.write_then_readinto(bytearray([0x40]), key_data)

        mask = key_data[0]
        btn_bits = [1 << 2, 1 << 3, 1 << 4]
        now = time.monotonic()
        self._last_update = now

        for i in range(3):
            if mask & btn_bits[i]:
                self._last_active[i] = now
            currently_held = (now - self._last_active[i]) < self._release_timeout

            if currently_held and not self._held[i]:
                self._pressed[i] = True
                self._released[i] = False
                self._held[i] = True
                self.events._push(ButtonEvent(i, True, now))
            elif not currently_held and self._held[i]:
                self._pressed[i] = False
                self._released[i] = True
                self._held[i] = False
                self.events._push(ButtonEvent(i, False, now))
            else:
                self._pressed[i] = False
                self._released[i] = False

    def _auto_update(self):
        # Rapid successive reads (e.g. draining the event queue) coalesce into
        # one hardware poll so a single tick sees a consistent snapshot.
        if time.monotonic() - self._last_update >= self._auto_update_throttle:
            self.update()

    @property
    def pressed(self):
        """True for one tick when a button transitions from up to down."""
        self._auto_update()
        return list(self._pressed)

    @property
    def released(self):
        """True for one tick when a button transitions from down to up."""
        self._auto_update()
        return list(self._released)

    @property
    def held(self):
        """True while a button is currently down."""
        self._auto_update()
        return list(self._held)