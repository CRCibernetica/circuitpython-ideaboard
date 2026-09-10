import time
from sumobotv2 import SumoBotV2

sumo = SumoBotV2()

# Read the accelerometer
ax,ay,az = sumo.accel
print(f"ax={ax}, ay={ay}, az={az}")

# Read the gyrocope
gx,gy,gz = sumo.gyro
print(f"gx={gx}, gy={gy}, gz={gz}")

# Read all four infrared sensors
s1, s2, s3, s4 = sumo.infrared
print(f"s1={s1}, s2={s2}, s3={s3}, s4={s4}")

# Turn LED RED on, then turn it off
# Note that the LED may be left on and does not interfere with the sumo.color() and sumo.raw_color()
# functions
print("LED=RED")
sumo.led = (255,0,0)
print("waiting...")
time.sleep(1.0)
print("LED=OFF")
sumo.led = (0,0,0)

# Read light detector manually
detector = sumo.detector
print(f"detector={detector}")

# Get surface color reading (normalized)
r,g,b = sumo.color()
print(f"r={r}, g={g}, b={b}")

# Get surface color reading (raw values)
dark,r,g,b = sumo.raw_color()
print(f"dark={dark}, r={r}, g={g}, b={b}")

