#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["pyserial>=3.5"]
# ///
"""
ibserial.py - talk to a CRCibernetica IdeaBoard over the USB serial REPL.

The IdeaBoard (ESP32 + CH340) never shows up as a CIRCUITPY drive, so tools
that expect a drive (file managers, circup) cannot reach it. This script does
what Thonny and IdeaCode do internally: it opens the serial port, switches
CircuitPython into the raw REPL, and runs small Python snippets on the board to
list, copy and delete files or to run a program and stream its output.

Only pyserial is needed. Any of these work:

    uv run tools/ibserial.py info            # uv installs pyserial on the fly
    pip install pyserial && python tools/ibserial.py info

Commands (REMOTE paths are absolute on the board, e.g. /lib/adafruit_bme280):

    info                       CircuitPython version, board id, free flash, /lib contents
    ls [REMOTE]                list a directory (default /), sizes in bytes, dirs end in /
    put LOCAL [REMOTE]         copy a file or a whole folder to the board
                               (default REMOTE is /<basename of LOCAL>)
    get REMOTE [LOCAL]         copy a file from the board (default LOCAL is the basename)
    rm REMOTE                  delete a file or a folder (recursive)
    cat REMOTE                 print a text file from the board
    run LOCAL.py               run a local script on the board and stream its output
                               (Ctrl-C stops it; nothing is saved on the board)
    exec "CODE"                run a snippet, e.g. exec "import os; print(os.listdir('/lib'))"
    scan                       scan the I2C bus (SDA=IO21, SCL=IO22) and print addresses
    reset                      soft-reboot so code.py starts again

Options:

    --port PORT                serial port; otherwise the CH340 is found automatically.
                               Linux: /dev/ttyUSB0  macOS: /dev/cu.wchusbserial*  Windows: COM3
                               The IBSERIAL_PORT environment variable does the same.

Only one program can hold the port. Close IdeaCode or Thonny before using this
script, and vice versa. For an interactive REPL use Thonny, IdeaCode or:

    python -m serial.tools.miniterm PORT 115200
"""

import argparse
import base64
import os
import posixpath
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("pyserial is missing. Run:  pip install pyserial   (or use: uv run tools/ibserial.py)")

BAUD = 115200
# USB vendor/product ids of the serial chips used on the IdeaBoard.
KNOWN_CHIPS = {
    (0x1A86, 0x7523): "CH340",
    (0x1A86, 0x55D4): "CH9102",
    (0x10C4, 0xEA60): "CP210x",
}
CHUNK = 768  # bytes per write when copying files (becomes 1024 base64 chars)


# ---------------------------------------------------------------- port discovery

def find_port(explicit=None):
    if explicit:
        return explicit
    env = os.environ.get("IBSERIAL_PORT")
    if env:
        return env
    ports = list(list_ports.comports())
    known = [p for p in ports if (p.vid, p.pid) in KNOWN_CHIPS]
    if len(known) == 1:
        return known[0].device
    if len(known) > 1:
        names = ", ".join(p.device for p in known)
        sys.exit("Several boards found (%s). Choose one with --port." % names)
    usb = [p for p in ports if p.vid is not None]
    if len(usb) == 1:
        return usb[0].device
    if not ports:
        sys.exit("No serial ports found. Is the IdeaBoard plugged in? (Check the USB cable carries data.)")
    listing = "\n".join("  %s  %s" % (p.device, p.description) for p in ports)
    sys.exit("Could not identify the IdeaBoard. Ports seen:\n%s\nUse --port to pick one." % listing)


# ---------------------------------------------------------------- raw REPL driver

class Board:
    def __init__(self, port):
        self.port = port
        try:
            self.ser = serial.Serial(port, BAUD, timeout=0.2, write_timeout=5)
        except serial.SerialException as e:
            msg = str(e)
            hint = ""
            if "Permission" in msg or "denied" in msg.lower():
                hint = ("\nOn Linux add yourself to the port's group (uucp on Arch, dialout on "
                        "Debian/Ubuntu) and log in again.")
            elif "busy" in msg.lower() or "in use" in msg.lower() or "Access is denied" in msg:
                hint = "\nAnother program has the port. Close IdeaCode or Thonny and try again."
            sys.exit("Could not open %s: %s%s" % (port, msg, hint))

    # low level -----------------------------------------------------------

    def _read_until(self, marker, timeout):
        """Read until `marker` appears; return everything before it."""
        buf = bytearray()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            b = self.ser.read(1)
            if b:
                buf += b
                if buf.endswith(marker):
                    return bytes(buf[: -len(marker)])
            elif self.ser.in_waiting == 0:
                continue
        raise TimeoutError("timeout waiting for %r; got %r" % (marker, bytes(buf[-200:])))

    def _write(self, data):
        # The CH340 has no flow control; pace writes like pyboard.py does.
        for i in range(0, len(data), 256):
            self.ser.write(data[i : i + 256])
            time.sleep(0.01)

    def enter_raw(self):
        self.ser.write(b"\r\x03\x03")  # stop code.py
        time.sleep(0.3)
        self.ser.reset_input_buffer()
        self.ser.write(b"\r\x01")  # Ctrl-A: raw REPL
        try:
            self._read_until(b"raw REPL; CTRL-B to exit\r\n>", 3)
        except TimeoutError:
            # A board that is mid-boot or printing a lot may need a second try.
            self.ser.write(b"\r\x03\x03")
            time.sleep(0.5)
            self.ser.reset_input_buffer()
            self.ser.write(b"\r\x01")
            self._read_until(b"raw REPL; CTRL-B to exit\r\n>", 5)

    def exit_raw(self):
        self.ser.write(b"\r\x02")  # Ctrl-B: friendly REPL
        time.sleep(0.1)

    def close(self):
        self.ser.close()

    def exec(self, code, timeout=15):
        """Run `code` in the raw REPL. Return stdout text; raise on a traceback."""
        if isinstance(code, str):
            code = code.encode()
        self._write(code + b"\x04")
        self._read_until(b"OK", 5)
        out = self._read_until(b"\x04", timeout)
        err = self._read_until(b"\x04", 5)
        self._read_until(b">", 2)
        if err:
            raise RuntimeError(err.decode(errors="replace").replace("\r", "").strip())
        return out.decode(errors="replace").replace("\r", "")

    def stream(self, code):
        """Run `code` and print its output live until it finishes or Ctrl-C."""
        if isinstance(code, str):
            code = code.encode()
        self._write(code + b"\x04")
        self._read_until(b"OK", 5)
        buf = bytearray()
        try:
            while True:
                b = self.ser.read(1)
                if not b:
                    continue
                if b == b"\x04":
                    break
                sys.stdout.write(b.decode(errors="replace"))
                sys.stdout.flush()
        except KeyboardInterrupt:
            self.ser.write(b"\x03")
            try:
                rest = self._read_until(b"\x04", 3)
                sys.stdout.write(rest.decode(errors="replace"))
            except TimeoutError:
                pass
        try:
            err = self._read_until(b"\x04", 3)
            self._read_until(b">", 2)
        except TimeoutError:
            err = b""
        if err:
            text = err.decode(errors="replace")
            if "KeyboardInterrupt" not in text:
                sys.stdout.write(text)
        sys.stdout.flush()

    # file helpers ---------------------------------------------------------

    def stat(self, path):
        """Return 'file', 'dir' or None."""
        out = self.exec(
            "import os\n"
            "try:\n"
            "    print('dir' if os.stat(%r)[0] & 0x4000 else 'file')\n"
            "except OSError:\n"
            "    print('none')\n" % path
        ).strip()
        return None if out == "none" else out

    def listdir(self, path):
        out = self.exec(
            "import os\n"
            "for n in sorted(os.listdir(%r)):\n"
            "    s = os.stat(%r + '/' + n)\n"
            "    print(n + ('/' if s[0] & 0x4000 else ''), s[6])\n" % (path, path.rstrip("/"))
        )
        items = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            name, size = line.rsplit(" ", 1)
            items.append((name, int(size)))
        return items

    def mkdir(self, path):
        self.exec(
            "import os\n"
            "try:\n"
            "    os.mkdir(%r)\n"
            "except OSError:\n"
            "    pass\n" % path
        )

    def put_file(self, local, remote):
        data = open(local, "rb").read()
        self.exec("f = open(%r, 'wb')" % remote)
        for i in range(0, len(data), CHUNK):
            b64 = base64.b64encode(data[i : i + CHUNK]).decode()
            self.exec("import binascii\nf.write(binascii.a2b_base64(%r))" % b64)
        size = int(self.exec("f.close()\nimport os\nprint(os.stat(%r)[6])" % remote).strip())
        if size != len(data):
            raise RuntimeError("size mismatch for %s: wrote %d, board has %d" % (remote, len(data), size))
        return size

    def put(self, local, remote):
        if os.path.isdir(local):
            self.mkdir(remote)
            for name in sorted(os.listdir(local)):
                if name.startswith(".") or name == "__pycache__":
                    continue
                self.put(os.path.join(local, name), posixpath.join(remote, name))
        else:
            size = self.put_file(local, remote)
            print("  %s  (%d bytes)" % (remote, size))

    def get_file(self, remote):
        out = self.exec(
            "import binascii\n"
            "f = open(%r, 'rb')\n"
            "while True:\n"
            "    c = f.read(%d)\n"
            "    if not c:\n"
            "        break\n"
            "    print(binascii.b2a_base64(c).decode().strip())\n"
            "f.close()\n" % (remote, CHUNK),
            timeout=60,
        )
        return b"".join(base64.b64decode(line) for line in out.split())

    def rm(self, remote):
        kind = self.stat(remote)
        if kind is None:
            sys.exit("%s does not exist on the board" % remote)
        self.exec(
            "import os\n"
            "def rm(p):\n"
            "    if os.stat(p)[0] & 0x4000:\n"
            "        for n in os.listdir(p):\n"
            "            rm(p + '/' + n)\n"
            "        os.rmdir(p)\n"
            "    else:\n"
            "        os.remove(p)\n"
            "rm(%r)\n" % remote,
            timeout=60,
        )


# ---------------------------------------------------------------- commands

def cmd_info(b, a):
    print(b.exec(
        "import os, sys\n"
        "u = os.uname()\n"
        "print('CircuitPython', u.release, 'on', sys.implementation._machine)\n"
        "print('board_id:', __import__('board').board_id)\n"
        "s = os.statvfs('/')\n"
        "print('flash free:', s[0]*s[3]//1024, 'KB of', s[0]*s[2]//1024, 'KB')\n"
    ), end="")
    print("port:", b.port)
    print("/lib:")
    for name, size in b.listdir("/lib"):
        print("  %-32s %6d" % (name, size) if not name.endswith("/") else "  %s" % name)


def cmd_ls(b, a):
    path = a.remote or "/"
    if b.stat(path) != "dir":
        sys.exit("%s is not a directory on the board" % path)
    for name, size in b.listdir(path):
        print("  %-32s %6d" % (name, size) if not name.endswith("/") else "  %s" % name)


def cmd_put(b, a):
    local = a.local
    if not os.path.exists(local):
        sys.exit("%s not found" % local)
    remote = a.remote or "/" + os.path.basename(os.path.normpath(local))
    parent = posixpath.dirname(remote.rstrip("/")) or "/"
    if parent != "/" and b.stat(parent) is None:
        b.mkdir(parent)
    print("Copying to %s" % remote)
    b.put(local, remote)
    print("Done.")


def cmd_get(b, a):
    if b.stat(a.remote) != "file":
        sys.exit("%s is not a file on the board" % a.remote)
    local = a.local or posixpath.basename(a.remote)
    data = b.get_file(a.remote)
    with open(local, "wb") as f:
        f.write(data)
    print("Saved %s (%d bytes)" % (local, len(data)))


def cmd_rm(b, a):
    b.rm(a.remote)
    print("Removed %s" % a.remote)


def cmd_cat(b, a):
    if b.stat(a.remote) != "file":
        sys.exit("%s is not a file on the board" % a.remote)
    sys.stdout.write(b.get_file(a.remote).decode(errors="replace"))


def cmd_run(b, a):
    code = open(a.local, "rb").read()
    b.stream(code)


def cmd_exec(b, a):
    b.stream(a.code)


def cmd_scan(b, a):
    print(b.exec(
        "import board\n"
        "i2c = board.I2C()\n"
        "while not i2c.try_lock():\n"
        "    pass\n"
        "found = i2c.scan()\n"
        "i2c.unlock()\n"
        "i2c.deinit()\n"
        "print('I2C devices:', [hex(x) for x in found] if found else 'none found')\n"
    ), end="")


def cmd_reset(b, a):
    b.exit_raw()
    b.ser.write(b"\x04")  # Ctrl-D in the friendly REPL = soft reboot, runs code.py
    print("Soft reboot sent; code.py is starting.")
    b.close()
    sys.exit(0)


def main():
    p = argparse.ArgumentParser(
        prog="ibserial.py",
        description="Talk to an IdeaBoard over the USB serial REPL. See the source docstring for details.",
    )
    p.add_argument("--port", help="serial port (default: auto-detect the CH340)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info").set_defaults(fn=cmd_info)
    s = sub.add_parser("ls"); s.add_argument("remote", nargs="?"); s.set_defaults(fn=cmd_ls)
    s = sub.add_parser("put"); s.add_argument("local"); s.add_argument("remote", nargs="?"); s.set_defaults(fn=cmd_put)
    s = sub.add_parser("get"); s.add_argument("remote"); s.add_argument("local", nargs="?"); s.set_defaults(fn=cmd_get)
    s = sub.add_parser("rm"); s.add_argument("remote"); s.set_defaults(fn=cmd_rm)
    s = sub.add_parser("cat"); s.add_argument("remote"); s.set_defaults(fn=cmd_cat)
    s = sub.add_parser("run"); s.add_argument("local"); s.set_defaults(fn=cmd_run)
    s = sub.add_parser("exec"); s.add_argument("code"); s.set_defaults(fn=cmd_exec)
    sub.add_parser("scan").set_defaults(fn=cmd_scan)
    sub.add_parser("reset").set_defaults(fn=cmd_reset)
    if len(sys.argv) == 1:
        print(__doc__.strip())
        sys.exit(0)
    a = p.parse_args()

    board = Board(find_port(a.port))
    try:
        board.enter_raw()
        a.fn(board, a)
    except TimeoutError as e:
        sys.exit("The board did not answer: %s\nPress RESET on the board and try again." % e)
    except RuntimeError as e:
        sys.exit("Error on the board:\n%s" % e)
    finally:
        try:
            board.exit_raw()
            board.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
