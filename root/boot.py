# boot.py — copy to CIRCUITPY/boot.py, ships alongside sumobot.py.
#
# Disables CircuitPython's built-in BLE workflow so user code owns the
# radio cleanly. Without this, the workflow advertises alongside our
# NUS advertisement and Windows centrals attach through the workflow's
# path, leaving our connection invisible to _bleio.adapter.connections.

import supervisor

supervisor.runtime.ble_workflow = False
