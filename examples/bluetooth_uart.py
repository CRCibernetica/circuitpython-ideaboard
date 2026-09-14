from adafruit_ble import BLERadio

from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

# set up the radio hardware
ble = BLERadio()

# By default, your device will have some name like CIRCUITPYxxxx; let's make that more user friendly
ble.name = "IdeaBoard_BLE"

# set up the UART service. This virtual serial port lets you send text over BLE.
uart = UARTService()

# set up advertising, so your phone or PC will know that UART service is available on your device
advertisement = ProvideServicesAdvertisement(uart)

while True:
  print("Advertising BLE services")
  # start advertising
  ble.start_advertising(advertisement)
  # keep going until we get a connection
  while not ble.connected:
    pass
    
  # if we got here, we have a connection. Stop advertising!
  ble.stop_advertising()
  print("BLE connected")
  
  # do some work as long as we're connected
  while ble.connected:
    # try reading some text from the UART, e.g. typed into the app
    raw_bytes = uart.readline()
    if raw_bytes:
      text = raw_bytes.decode("utf-8")
      print(f"Got text from central: {text}")
      # reverse the text and echo it back!
      flipped = "".join(reversed(text[:-1]))
      uart.write(flipped.encode("utf-8"))
  
  # we no longer have a connection, so we'll go back to the top of the loop
  # and start advertising again
  print("BLE disconnected")