from machine import ADC, UART, Pin, Timer

try:
    from ptzpicocam.camera import *
except ImportError:
    from camera import *

TESTING = False

JOYX_PIN = ADC(Pin(26))
JOYY_PIN = ADC(Pin(27))
ZOOM_PIN = ADC(Pin(28))


class Camera:

    def __init__(self) -> None:
        self.pan_speed = 1
        self.pan_dir = PanDirection.NONE

        self.tilt_speed = 1
        self.tilt_dir = PanDirection.NONE

        self.zoom_speed = 1
        self.zoom_dir = ZoomDirection.NONE


class Joystick:

    def __init__(self, min_adc_val: int, max_adc_val: int, deadzone: int) -> None:
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
        center = self.max_adc_val // 2
        threshold = center * joystick.deadzone // 100

        self.left_limit = center - threshold
        self.right_limit = center + threshold


def convert_joyx_to_pan(joystick: 'Joystick', camera: 'Camera') -> bool:
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


def loop(joystick: 'Joystick', camera: 'Camera', uart):
    buffer = bytearray(16)
    ZOOM_LED_PIN = Pin(5, Pin.OUT)

    while True:
        if joystick.read_joystick_flag:
            joystick.read_joystick_flag = False

            joystick.x = JOYX_PIN.read_u16()
            joystick.y = JOYY_PIN.read_u16()
            joystick.zoom = ZOOM_PIN.read_u16()

            convert_joyx_to_pan(joystick, camera)
            convert_joyy_to_tilt(joystick, camera)
            zoom_in_deadzone = convert_zoom(joystick, camera)

            if zoom_in_deadzone:
                ZOOM_LED_PIN.on()
            else:
                ZOOM_LED_PIN.off()

            #pan_tilt_packet = CameraAPI.create_pan_tilt_packet(buffer, camera.pan_speed, camera.pan_dir, camera.tilt_speed, camera.tilt_dir)
            #uart.write(pan_tilt_packet.encode())
            print(camera.pan_speed, zoom_in_deadzone)


def timer_isr(joystick: 'Joystick'):
    joystick.read_joystick_flag = True


if __name__ == '__main__':
    camera = Camera()

    joystick = Joystick(0, 0xffff, 5)
    joystick.compute_bounds()

    timer0 = Timer()
    timer0.init(freq=30, mode=Timer.PERIODIC, callback=lambda t: timer_isr(joystick))

    uart1 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

    if not TESTING:
        loop(joystick, camera, uart1)
