import sys
import time
from unittest import TestCase
from unittest.mock import MagicMock

from ptzpicocam.camera import PanDirection, TiltDirection, ZoomDirection

sys.modules['machine'] = MagicMock()
from ptzpicocam.pico import (Button, ButtonPressType, Camera, Joystick,
                             convert_joyx_to_pan, convert_joyy_to_tilt,
                             convert_zoom)


class TestButton(TestCase):

    def setUp(self) -> None:
        self.time_mock = MagicMock()
        time.ticks_ms = self.time_mock

    def test_isr_Should_NotUpdateFlag_When_ReboundDetected(self):
        self.time_mock.return_value = 0
        button = Button()
        button.triggered_flag = False

        button.isr()

        self.assertFalse(button.triggered_flag)

    def test_isr_Should_UpdateFlag_When_NoReboundDetected(self):
        self.time_mock.return_value = 10000
        button = Button()
        button.last_pressed_time = 9000

        button.isr()

        self.assertTrue(button.triggered_flag)
        self.assertEqual(10000, button.last_pressed_time)

    def test_press_type_Should_ReturnNone_When_ButtonNotPressed(self):
        button = Button()
        button.pressed = False

        result = button.press_type

        self.assertEqual(ButtonPressType.NONE, result)

    def test_press_type_Should_ReturnShort_When_PressLTLimit(self):
        self.time_mock.return_value = 10000
        button = Button()
        button.pressed = True
        button.time_pressed = 10000 - Button.LONG_PRESS_TIME + 1

        result = button.press_type

        self.assertEqual(ButtonPressType.SHORT_PRESS, result)

    def test_press_type_Should_ReturnLong_When_PressGTLimit(self):
        self.time_mock.return_value = 10000
        button = Button()
        button.pressed = True
        button.time_pressed = 10000 - Button.LONG_PRESS_TIME

        result = button.press_type

        self.assertEqual(ButtonPressType.LONG_PRESS, result)


class TestJoystick(TestCase):

    def test_compute_bounds_When_GivenDeadzoneZero(self):
        with self.subTest('With even maximum adc value'):
            joystick = Joystick(0, 100, 0)
            joystick.compute_bounds()

            self.assertEqual(50, joystick.left_limit)
            self.assertEqual(50, joystick.right_limit)

        with self.subTest('With odd maximum adc value'):
            joystick = Joystick(0, 99, 0)
            joystick.compute_bounds()

            self.assertEqual(49, joystick.left_limit)
            self.assertEqual(49, joystick.right_limit)


class TestJoyXConversion(TestCase):

    def setUp(self) -> None:
        self.joystick = Joystick(0, 100, 0)
        self.joystick.left_limit = 50
        self.joystick.right_limit = 50

    def test_convert_joyx_to_pan(self):
        camera = Camera()

        with self.subTest('When joyx is in the middle'):
            self.joystick.x = 50
            in_deadzone = convert_joyx_to_pan(self.joystick, camera)

            self.assertTrue(in_deadzone)
            self.assertEqual(1, camera.pan_speed)
            self.assertEqual(PanDirection.NONE, camera.pan_dir)

        with self.subTest('When joyx is in the left side'):
            self.joystick.x = 35
            in_deadzone = convert_joyx_to_pan(self.joystick, camera)

            self.assertFalse(in_deadzone)
            self.assertLess(0, camera.pan_speed)
            self.assertGreater(0x24, camera.pan_speed)
            self.assertEqual(PanDirection.RIGHT, camera.pan_dir)

        with self.subTest('When joyy is in the right side'):
            self.joystick.x = 81
            in_deadzone = convert_joyx_to_pan(self.joystick, camera)

            self.assertFalse(in_deadzone)
            self.assertLess(0, camera.pan_speed)
            self.assertGreater(0x24, camera.pan_speed)
            self.assertEqual(PanDirection.LEFT, camera.pan_dir)

    def test_convert_joyy_to_pan(self):
        camera = Camera()

        with self.subTest('When joyy is in the middle'):
            self.joystick.y = 50
            in_deadzone = convert_joyy_to_tilt(self.joystick, camera)

            self.assertTrue(in_deadzone)
            self.assertEqual(1, camera.tilt_speed)
            self.assertEqual(TiltDirection.NONE, camera.tilt_dir)

        with self.subTest('When joyy is in the left side'):
            self.joystick.y = 35
            in_deadzone = convert_joyy_to_tilt(self.joystick, camera)

            self.assertFalse(in_deadzone)
            self.assertLess(0, camera.tilt_speed)
            self.assertGreater(0x23, camera.tilt_speed)
            self.assertEqual(TiltDirection.UP, camera.tilt_dir)

        with self.subTest('When joyy is in the right side'):
            self.joystick.y = 81
            in_deadzone = convert_joyy_to_tilt(self.joystick, camera)

            self.assertFalse(in_deadzone)
            self.assertLess(0, camera.tilt_speed)
            self.assertGreater(0x23, camera.tilt_speed)
            self.assertEqual(TiltDirection.DOWN, camera.tilt_dir)

    def test_convert_zoom(self):
        camera = Camera()

        with self.subTest('When zoom is in the middle'):
            self.joystick.zoom = 50
            in_deadzone = convert_zoom(self.joystick, camera)

            self.assertTrue(in_deadzone)
            self.assertEqual(1, camera.zoom_speed)
            self.assertEqual(ZoomDirection.NONE, camera.zoom_dir)

        with self.subTest('When zoom is in the left side'):
            self.joystick.zoom = 35
            in_deadzone = convert_zoom(self.joystick, camera)

            self.assertFalse(in_deadzone)
            self.assertLess(0, camera.zoom_speed)
            self.assertGreater(0x23, camera.zoom_speed)
            self.assertEqual(ZoomDirection.WIDE, camera.zoom_dir)

        with self.subTest('When zoom is in the right side'):
            self.joystick.zoom = 81
            in_deadzone = convert_zoom(self.joystick, camera)

            self.assertFalse(in_deadzone)
            self.assertLess(0, camera.zoom_speed)
            self.assertGreater(0x23, camera.zoom_speed)
            self.assertEqual(ZoomDirection.TELE, camera.zoom_dir)
