# Shows why HTTPS fails with MemoryError once the IdeaSense library is loaded.
#
# TLS (https://) needs one free block of about 18 to 20 KB in the ESP-IDF heap.
# The Python heap grows into that same memory when libraries are imported and
# never gives it back. gc.mem_free() still reports plenty free, so watch
# espidf.heap_caps_get_largest_free_block() instead.
#
# Expected on CircuitPython 10.3.0: before IdeaSense the largest block is about
# 48 KB; after it about 13 KB. http:// works, https:// raises MemoryError.
# Needs secrets.py with "ssid" and "password".

import gc
import espidf
import wifi
import socketpool
import ssl
import adafruit_requests
from secrets import secrets

URL = "api.open-meteo.com/v1/forecast?latitude=9.93&longitude=-84.08&current=temperature_2m"


def mem(tag):
    gc.collect()
    print(f"{tag:22s} gc_free={gc.mem_free():6d} "
          f"idf_free={espidf.heap_caps_get_free_size():6d} "
          f"idf_largest={espidf.heap_caps_get_largest_free_block():6d}")


def get(scheme):
    try:
        r = requests.get(scheme + "://" + URL)
        print(scheme, "ok:", r.json()["current"]["temperature_2m"], "C")
        r.close()
    except MemoryError:
        print(scheme, "failed: MemoryError")


mem("start")
from ideasense import IdeaSense
from font5x5 import TextDisplay
idea = IdeaSense()
display = TextDisplay(idea.matrix)
mem("IdeaSense loaded")

wifi.radio.connect(secrets["ssid"], secrets["password"])
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
mem("Wi-Fi connected")

get("http")
get("https")
mem("end")
