import board
from neopixel import NeoPixel
from rainbowio import colorwheel
import pwmio
from simpleio import map_range
from adafruit_motor import servo, motor


class IdeaBoard:
    def __init__(self):
        self._brightness = 0.3
        self._np = NeoPixel(board.NEOPIXEL, 1, brightness=self._brightness, auto_write=True)
        self._np[0] = (0,0,0)
        self._m1a = pwmio.PWMOut(board.IO12, duty_cycle=0, frequency=50)
        self._m1b = pwmio.PWMOut(board.IO14, duty_cycle=0, frequency=50)
        self._m2a = pwmio.PWMOut(board.IO13, duty_cycle=0, frequency=50)
        self._m2b = pwmio.PWMOut(board.IO15, duty_cycle=0, frequency=50)
        self.motor_1 = motor.DCMotor(self._m1a, self._m1b)
        self.motor_2 = motor.DCMotor(self._m2a, self._m2b)
        self.map_range = map_range
    
    
    @property
    def pixel(self):
        return self._np[0]
    
    
    @pixel.setter
    def pixel(self, color=(0,0,0)):
        self._np[0] = color
    
    
    @property
    def brightness(self):
        return self._brightness
    
    
    @brightness.setter
    def brightness(self, new_brightness):
        if new_brightness <= 1 or new_brightness >= 0:
            self._brightness = new_brightness
            self._np.brightness = self._brightness
   
   
    @property
    def arcoiris(self):
        return self._np[0]
 
 
    @arcoiris.setter
    def arcoiris(self, n=0):
        color = colorwheel(n)
        self.pixel = color 


#     def motor_1(self, vel=0):
#         vel = int(map_range(vel, -255, 255, -65535, 65535))
#         if vel < -65535 | vel > 65535:
#             print(f"velocidad no valida: {vel}")
#         if vel >= 0:
#             self._m1a.duty_cycle = vel
#             self._m1b.duty_cycle = 0
#         if vel < 0:
#             self._m1a.duty_cycle = 0
#             self._m1b.duty_cycle = (vel * -1)
#     
#     def motor_2(self, vel=0):
#         vel = int(map_range(vel, -255, 255, -65535, 65535))
#         if vel < -65535 | vel > 65535:
#             print(f"velocidad no valida: {vel}")
#         if vel >= 0:
#             self._m2a.duty_cycle = vel
#             self._m2b.duty_cycle = 0
#         if vel < 0:
#             self._m2a.duty_cycle = 0
#             self._m2b.duty_cycle = (vel * -1)
        
        
    class Servo:
        """
        A simple class for controlling hobby servos.

        Args:
            pin: The pin where servo is connected. Must support PWM.
            freq (int): The frequency of the signal, in hertz.
            min_us (int): The minimum signal length supported by the servo.
            max_us (int): The maximum signal length supported by the servo.
            max_angle (int): The angle between the minimum and maximum positions.

        """
        def __init__(self, pin, freq=50, min_pulse = 500, max_pulse = 2500):
            self.min_pulse = min_pulse
            self.max_pulse = max_pulse
            self.us = 0
            self.freq = freq
            self._angle = 0
            self.pwm = pwmio.PWMOut(pin, duty_cycle=2 ** 15, frequency=freq)
            self.servo = servo.Servo(self.pwm, min_pulse = self.min_pulse, max_pulse = self.max_pulse)

        @property
        def angle(self):
            return self._angle
        
        @angle.setter
        def angle(self, new_angle):
            """Move to the specified angle in ``degrees``."""
            self._angle = new_angle
            self.servo.angle = self._angle
            
