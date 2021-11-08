from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock

from ptzpicocam.visca import RawViscaPacket

from ptzsimcam.camera_server import (handle_memory_packet,
                                     handle_pan_tilt_packet,
                                     handle_zoom_packet)


def create_packet(data: bytes) -> 'RawViscaPacket':
    return RawViscaPacket(1, 0, bytearray(data))


class TestHandleMemoryPacket(TestCase):

    def create_memory_packet(self, action: int, position_index: int) -> 'RawViscaPacket':
        data = bytearray(b'\x01\x04\x3f')
        data.append(action)
        data.append(position_index)

        return RawViscaPacket(1, 0, data)

    def test_handle_memory_packet_Should_ReturnFalse_When_GivenInvalidPacket(self):
        empty_packet = create_packet(b'')
        result = handle_memory_packet(MagicMock(), empty_packet)
        self.assertFalse(result)

        invalid_packet = create_packet(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        result = handle_memory_packet(MagicMock(), invalid_packet)
        self.assertFalse(result)

    def test_handle_memory_packet_Should_ReturnFalse_When_GivenInvalidPositionIndex(self):
        packet = self.create_memory_packet(1, 10)
        result = handle_memory_packet(MagicMock(), packet)
        self.assertFalse(result)

    def test_handle_memory_packet_Should_ReturnFalse_When_GivenInvalidAction(self):
        packet = self.create_memory_packet(5, 1)
        result = handle_memory_packet(MagicMock(), packet)
        self.assertFalse(result)

    def test_handle_memory_packet_Should_ReturnTrue_When_GivenValidPacket(self):
        packet = self.create_memory_packet(1, 1)
        result = handle_memory_packet(MagicMock(), packet)
        self.assertTrue(result)

    def test_handle_memory_packet(self):
        camera = MagicMock()

        with self.subTest('Should reset positions when given reset action'):
            packet = self.create_memory_packet(0, 1)
            handle_memory_packet(camera, packet)

            camera.reset_positions.assert_called()

        with self.subTest('Should set position when given set action'):
            packet = self.create_memory_packet(1, 1)
            handle_memory_packet(camera, packet)

            camera.set_position.assert_called_with(1)

        with self.subTest('Should recall position when given recall action'):
            packet = self.create_memory_packet(2, 1)
            handle_memory_packet(camera, packet)

            camera.recall_position.assert_called_with(1)


class TestHandlePanTiltPacket(TestCase):

    def create_pan_tilt_packet(self, pan_speed: int, pan_direction: int, tilt_speed: int, tilt_direction: int) -> 'RawViscaPacket':
        data = bytearray(b'\x01\x06\x01')
        data.append(pan_speed)
        data.append(tilt_speed)
        data.append(pan_direction)
        data.append(tilt_direction)

        return RawViscaPacket(1, 0, data)

    def test_handle_pan_tilt_packet_Should_ReturnFalse_When_GivenInvalidPacket(self):
        empty_packet = create_packet(b'')
        result = handle_pan_tilt_packet(MagicMock(), empty_packet)
        self.assertFalse(result)

        invalid_packet = create_packet(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        result = handle_pan_tilt_packet(MagicMock(), invalid_packet)
        self.assertFalse(result)

    def test_handle_pan_tilt_packet_Should_ReturnTrue_When_GivenValidPacket(self):
        packet = self.create_pan_tilt_packet(1, 1, 1, 1)
        result = handle_pan_tilt_packet(MagicMock(), packet)
        self.assertTrue(result)

    def test_handle_pan_tilt_packet(self):
        camera = MagicMock()
        pan_speed = PropertyMock()
        tilt_speed = PropertyMock()

        type(camera).pan_speed = pan_speed
        type(camera).tilt_speed = tilt_speed

        with self.subTest('Drive speed should be set to 0 when given invalid pan speed'):
            packet = self.create_pan_tilt_packet(34, 1, 2, 1)
            handle_pan_tilt_packet(camera, packet)

            pan_speed.assert_called_with(0)
            tilt_speed.assert_called_with(0)

        with self.subTest('Drive speed should be set to 0 when given invalid tilt speed'):
            packet = self.create_pan_tilt_packet(1, 1, 34, 1)
            handle_pan_tilt_packet(camera, packet)

            pan_speed.assert_called_with(0)
            tilt_speed.assert_called_with(0)

        with self.subTest('Pan speed should be set to 0 when given stop pan'):
            packet = self.create_pan_tilt_packet(3, 3, 1, 1)
            handle_pan_tilt_packet(camera, packet)

            pan_speed.assert_called_with(0)
            tilt_speed.assert_called()
            # Tilt speed must be set with a value greater than 0
            self.assertEqual(1, len(tilt_speed.call_args.args))
            self.assertLess(0, tilt_speed.call_args.args[0])

        with self.subTest('Tilt speed should be set to 0 when given stop tilt'):
            packet = self.create_pan_tilt_packet(1, 1, 3, 3)
            handle_pan_tilt_packet(camera, packet)

            pan_speed.assert_called()
            tilt_speed.assert_called_with(0)

            # Pan speed must be set with a value greater than 0
            self.assertEqual(1, len(pan_speed.call_args.args))
            self.assertLess(0, pan_speed.call_args.args[0])



class TestHandleZoomPacket(TestCase):

    def create_zoom_packet(self, direction: int, speed: int) -> 'RawViscaPacket':
        data = bytearray(b'\x01\x04\x07')
        data.append(direction << 4 | speed)

        return RawViscaPacket(1, 0, data)

    def test_handle_zoom_packet_Should_ReturnFalse_When_GivenInvalidPacket(self):
        empty_packet = create_packet(b'')
        result = handle_zoom_packet(MagicMock(), empty_packet)
        self.assertFalse(result)

        invalid_packet = create_packet(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        result = handle_zoom_packet(MagicMock(), invalid_packet)
        self.assertFalse(result)

    def test_handle_zoom_packet_Should_ReturnFalse_When_GivenInvalidData(self):
        zoom_attr = PropertyMock()
        camera = MagicMock()
        type(camera).zoom_speed = zoom_attr

        packet_with_invalid_speed = self.create_zoom_packet(2, 0)
        result = handle_zoom_packet(MagicMock(), packet_with_invalid_speed)
        self.assertFalse(result, 'Should return False when given invalid speed')

        packet_with_invalid_dir = self.create_zoom_packet(1, 4)
        result = handle_zoom_packet(MagicMock(), packet_with_invalid_dir)
        self.assertFalse(result, 'Should return False when given invalid direction')

        # Zoom speed should not been updated
        zoom_attr.assert_not_called()

    def test_handle_zoom_packet_Should_ReturnTrue_When_GivenValidPacket(self):
        valid_packet = self.create_zoom_packet(2, 2)
        result = handle_zoom_packet(MagicMock(), valid_packet)
        self.assertTrue(result)

    def test_handle_zoom_packet_Should_UpdateZoomSpeed(self):
        zoom_attr = PropertyMock()
        camera = MagicMock()
        type(camera).zoom_speed = zoom_attr

        with self.subTest('Camera zoom speed should be set to 0 when packet contains stop'):
            packet = self.create_zoom_packet(0, 3)
            handle_zoom_packet(camera, packet)
            zoom_attr.assert_called_with(0)

        with self.subTest('Camera zomm speed should be set to -3 when packet contains wide command'):
            packet = self.create_zoom_packet(2, 3)
            handle_zoom_packet(camera, packet)
            zoom_attr.assert_called_with(-3)
