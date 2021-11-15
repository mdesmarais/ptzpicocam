from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock

from ptzpicocam.camera import CameraAPI, PanDirection, TiltDirection
from ptzpicocam.visca import RawViscaPacket

from ptzsimcam.camera_server import (handle_memory_packet,
                                     handle_pan_tilt_packet,
                                     handle_zoom_packet)


def create_packet(data: bytes) -> 'RawViscaPacket':
    p = RawViscaPacket(1, 0, bytearray(b'\x00' + data + b'\x00'))
    p.data_size = len(data)

    return p


class TestHandleMemoryPacket(TestCase):

    def create_memory_packet(self, action: int, position_index: int) -> 'RawViscaPacket':
        p = RawViscaPacket(1, 0, bytearray(20))
        p.write_bytes(b'\x01\x04\x3f')
        p.write_data(action)
        p.write_data(position_index)

        return p

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

        with self.subTest('Should set memory when given set action'):
            packet = self.create_memory_packet(1, 1)
            handle_memory_packet(camera, packet)

            camera.set_memory.assert_called_with(1)

        with self.subTest('Should recall memory when given recall action'):
            packet = self.create_memory_packet(2, 1)
            handle_memory_packet(camera, packet)

            camera.recall_memory.assert_called_with(1)


class TestHandlePanTiltPacket(TestCase):

    def test_handle_pan_tilt_packet_Should_ReturnFalse_When_GivenInvalidPacket(self):
        empty_packet = create_packet(b'')
        result = handle_pan_tilt_packet(MagicMock(), empty_packet)
        self.assertFalse(result)

        invalid_packet = create_packet(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        result = handle_pan_tilt_packet(MagicMock(), invalid_packet)
        self.assertFalse(result)

    def test_handle_pan_tilt_packet_Should_ReturnTrue_When_GivenValidPacket(self):
        packet = CameraAPI.create_pan_tilt_packet(bytearray(20), 1, PanDirection.LEFT, 1, TiltDirection.UP)
        result = handle_pan_tilt_packet(MagicMock(), packet)
        self.assertTrue(result)

    def test_handle_pan_tilt_packet(self):
        camera = MagicMock()
        pan_speed = PropertyMock()
        tilt_speed = PropertyMock()

        type(camera).pan_speed = pan_speed
        type(camera).tilt_speed = tilt_speed

        with self.subTest('Drive speed should be set to 0 when given invalid pan speed'):
            packet = CameraAPI.create_pan_tilt_packet(bytearray(20), 1, PanDirection.LEFT, 2, TiltDirection.UP)
            # Forces invalid speed without triggering exception
            packet.data[3] = 34
            print(packet.buffer, packet.data.tobytes())
            handle_pan_tilt_packet(camera, packet)

            pan_speed.assert_called_with(0)
            tilt_speed.assert_called_with(0)

        with self.subTest('Drive speed should be set to 0 when given invalid tilt speed'):
            packet = CameraAPI.create_pan_tilt_packet(bytearray(20), 1, PanDirection.LEFT, 1, TiltDirection.UP)
            # Forces invalid speed without triggering exception
            packet.data[4] = 34
            handle_pan_tilt_packet(camera, packet)

            pan_speed.assert_called_with(0)
            tilt_speed.assert_called_with(0)

        with self.subTest('Pan speed should be set to 0 when given stop pan'):
            packet = CameraAPI.create_pan_tilt_packet(bytearray(20), 3, PanDirection.NONE, 1, TiltDirection.UP)
            handle_pan_tilt_packet(camera, packet)

            pan_speed.assert_called_with(0)
            tilt_speed.assert_called()
            # Tilt speed must be set with a value greater than 0
            self.assertEqual(1, len(tilt_speed.call_args.args))
            self.assertLess(0, tilt_speed.call_args.args[0])

        with self.subTest('Tilt speed should be set to 0 when given stop tilt'):
            packet = CameraAPI.create_pan_tilt_packet(bytearray(20), 1, PanDirection.LEFT, 3, TiltDirection.NONE)
            handle_pan_tilt_packet(camera, packet)

            pan_speed.assert_called()
            tilt_speed.assert_called_with(0)

            # Pan speed must be set with a value greater than 0
            self.assertEqual(1, len(pan_speed.call_args.args))
            self.assertLess(0, pan_speed.call_args.args[0])



class TestHandleZoomPacket(TestCase):

    def create_zoom_packet(self, direction: int, speed: int) -> 'RawViscaPacket':
        p = RawViscaPacket(1, 0, bytearray(20))
        p.write_bytes(b'\x01\x04\x07')
        p.write_data(direction << 4 | speed)

        return p

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
