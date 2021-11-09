import time

from machine import ADC, UART, Pin, Timer

try:
    from ptzpicocam.camera import *
except ImportError:
    from camera import *

TESTING = False # Should always be False when running on the device target

BTN1_PIN = Pin(10, Pin.IN)

JOYX_PIN = ADC(Pin(26))
JOYY_PIN = ADC(Pin(27))
ZOOM_PIN = ADC(Pin(28))


class Button:

    """A dummy button that supports short and press long detection."""

    def __init__(self):
        self.last_pressed_time = 0
        self.time_pressed = 0
        self.triggered_flag = False # Updated by an isr
        self.pressed = False

    def isr(self):
        """Called when a button pin detects a change (falling or rising edge).
        
        The isr prevents a rebound by saving the timestamp of the last call.
        """
        t = time.ticks_ms()

        if t - self.last_pressed_time > 25:
            self.last_pressed_time = t
            self.triggered_flag = True

    @property
    def press_type(self) -> 'ButtonPressType':
        """Gets the press type."""
        if self.pressed:
            # @TODO 1000 may be adapted
            if time.ticks_ms() - self.time_pressed < 1000:
                pt = ButtonPressType.SHORT_PRESS
            else:
                pt = ButtonPressType.LONG_PRESS
            self.pressed = False
        else:
            self.pressed = True
            self.time_pressed = time.ticks_ms()

            pt = ButtonPressType.NONE

        return pt


class ButtonPressType(IntEnum):

    """Reprents a button press type."""

    NONE = 0
    SHORT_PRESS = 1
    LONG_PRESS = 2


class Camera:

    """Structure containing informations to send to a camera."""

    def __init__(self) -> None:
        self.pan_speed = 1
        self.pan_dir = PanDirection.NONE

        self.tilt_speed = 1
        self.tilt_dir = PanDirection.NONE

        self.zoom_speed = 1
        self.zoom_dir = ZoomDirection.NONE


class Joystick:

    """Structure containing informations about a 3-axes joystick."""

    def __init__(self, min_adc_val: int, max_adc_val: int, deadzone: int) -> None:
        """Creates a new joystick structure.
        
        :param min_adc_val: minimal value returned by the device ADC
        :param max_adc_val: maximal value returned by the device ADC
        :param deadzone: deadzone in percentage based on the max_adc_val param
        """
        self.x = 0
        self.y = 0
        self.zoom = 0
        self.min_adc_val = min_adc_val
        self.max_adc_val = max_adc_val
        self.left_limit = 0
        self.right_limit = 0
        self.deadzone = deadzone
        self.read_joystick_flag = False

    def compute_bounds(self) -> None:
        """Computes left and right bounds according to the deadzone.
        
        Attributes :py:attr:`~.Joystick.left_limit` and :py:attr:`~.Joystick.right_limit` will be set.
        """
        center = self.max_adc_val // 2
        threshold = center * joystick.deadzone // 100

        self.left_limit = center - threshold
        self.right_limit = center + threshold


def convert_joyx_to_pan(joystick: 'Joystick', camera: 'Camera') -> bool:
    """Converts a joystick axe value into a camera value.
    
    Attributes :py:attr:`~.Camera.pan_dir` and :py:attr:`~.Camera.pan_speed`
    will be modified.
    
    :param joystick: instance of the joystick containing the value to convert
    :param camera: instance of the camera to update
    :returns: True if the joystick is in the deadzone, otherwise False
    """
    in_deadzone = False

    if joystick.x < joystick.left_limit:
        camera.pan_speed = convert_range(abs(joystick.x - joystick.left_limit), joystick.min_adc_val, joystick.left_limit, 1, 0x18)
        camera.pan_dir = PanDirection.RIGHT
    elif joystick.x > joystick.right_limit:
        camera.pan_speed = convert_range(joystick.x, joystick.right_limit, joystick.max_adc_val, 1, 0x18)
        camera.pan_dir = PanDirection.LEFT
    else:
        camera.pan_speed = 1
        camera.pan_dir = PanDirection.NONE
        in_deadzone = True

    return in_deadzone


def convert_joyy_to_tilt(joystick: 'Joystick', camera: 'Camera') -> bool:
    """Converts a joystick axe value into a camera value.
    
    Attributes :py:attr:`~.Camera.tilt_dir` and :py:attr:`~.Camera.tilt_speed`
    will be modified.
    
    :param joystick: instance of the joystick containing the value to convert
    :param camera: instance of the camera to update
    :returns: True if the joystick is in the deadzone, otherwise False
    """
    in_deadzone = False

    if joystick.y < joystick.left_limit:
        camera.tilt_speed = convert_range(abs(joystick.y - joystick.left_limit), joystick.min_adc_val, joystick.left_limit, 1, 0x17)
        camera.tilt_dir = TiltDirection.UP
    elif joystick.y > joystick.right_limit:
        camera.tilt_speed = convert_range(joystick.y, joystick.right_limit, joystick.max_adc_val, 1, 0x17)
        camera.tilt_dir = TiltDirection.DOWN
    else:
        camera.tilt_speed = 1
        camera.tilt_dir = TiltDirection.NONE
        in_deadzone = True

    return in_deadzone


def convert_zoom(joystick: 'Joystick', camera: 'Camera') -> bool:
    """Converts a joystick axe value into a camera value.
    
    Attributes :py:attr:`~.Camera.zoom_dir` and :py:attr:`~.Camera.zoom_speed`
    will be modified.
    
    :param joystick: instance of the joystick containing the value to convert
    :param camera: instance of the camera to update
    :returns: True if the joystick is in the deadzone, otherwise False
    """
    in_deadzone = False

    if joystick.zoom < joystick.left_limit:
        camera.zoom_speed = convert_range(abs(joystick.zoom - joystick.left_limit), joystick.min_adc_val, joystick.left_limit, 1, 7)
        camera.zoom_dir = ZoomDirection.WIDE
    elif joystick.zoom > joystick.right_limit:
        camera.zoom_speed = convert_range(joystick.zoom, joystick.right_limit, joystick.max_adc_val, 1, 7)
        camera.zoom_dir = ZoomDirection.TELE
    else:
        camera.zoom_speed = 1
        camera.zoom_dir = ZoomDirection.NONE
        in_deadzone = True

    return in_deadzone


def convert_range(value: int, old_min: int, old_max: int, new_min: int, new_max: int) -> int:
    return ((value - old_min) // (old_max - old_min)) * (new_max - new_min) + new_min


def loop(joystick: 'Joystick', camera: 'Camera', uart, btn1: 'Button') -> None:
    """Main loop.
    
    :param joystick: instance of a joystick
    :param camera: instance of a camera to control
    :param uart: uart for sending packets
    :param btn1: instance of a button
    """
    buffer = bytearray(16)
    ZOOM_LED_PIN = Pin(5, Pin.OUT)

    while True:
        if btn1.triggered_flag:
            btn1.triggered_flag = False
            
            press_type = btn1.press_type

            if press_type == ButtonPressType.SHORT_PRESS:
                print('short')
            elif press_type == ButtonPressType.LONG_PRESS:
                print('long')

        if joystick.read_joystick_flag:
            joystick.read_joystick_flag = False

            # Reads joystick values from ADC
            joystick.x = JOYX_PIN.read_u16()
            joystick.y = JOYY_PIN.read_u16()
            joystick.zoom = ZOOM_PIN.read_u16()

            convert_joyx_to_pan(joystick, camera)
            convert_joyy_to_tilt(joystick, camera)
            zoom_in_deadzone = convert_zoom(joystick, camera)

            if zoom_in_deadzone:
                ZOOM_LED_PIN.on()
                zoom_packet = CameraAPI.create_zoom_packet(buffer, camera.zoom_speed, camera.zoom_dir)
            else:
                ZOOM_LED_PIN.off()
                zoom_packet = CameraAPI.create_stop_zoom_packet(buffer)

            uart.write(zoom_packet.encode())

            pan_tilt_packet = CameraAPI.create_pan_tilt_packet(buffer, camera.pan_speed, camera.pan_dir, camera.tilt_speed, camera.tilt_dir)
            uart.write(pan_tilt_packet.encode())


def timer_isr(joystick: 'Joystick'):
    joystick.read_joystick_flag = True


if __name__ == '__main__':
    camera = Camera()

    joystick = Joystick(0, 0xffff, 5)
    joystick.compute_bounds()

    timer0 = Timer()
    timer0.init(freq=30, mode=Timer.PERIODIC, callback=lambda t: timer_isr(joystick))

    uart1 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

    btn1 = Button()
    BTN1_PIN.irq(lambda p: btn1.isr())

    if not TESTING:
        loop(joystick, camera, uart1, btn1)
