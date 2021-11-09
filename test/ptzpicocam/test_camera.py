from itertools import product
from unittest import TestCase
from unittest.mock import MagicMock, patch

from ptzpicocam.camera import (CameraAPI, MemoryAction, PanDirection,
                               TiltDirection, ZoomDirection)
from ptzpicocam.visca import RawViscaPacket


class TestCreateDrivePacket(TestCase):

    def test_create_pan_tilt_packet_Should_RaiseValueError_When_GivenInvalidSpeed(self):
        buffer = bytearray(20)

        with self.assertRaises(ValueError):
            CameraAPI.create_pan_tilt_packet(buffer, 0, PanDirection.LEFT, 1, TiltDirection.UP)

        with self.assertRaises(ValueError):
            CameraAPI.create_pan_tilt_packet(buffer, 25, PanDirection.LEFT, 1, TiltDirection.UP)

        with self.assertRaises(ValueError):
            CameraAPI.create_pan_tilt_packet(buffer, 1, PanDirection.LEFT, 0, TiltDirection.UP)

        with self.assertRaises(ValueError):
            CameraAPI.create_pan_tilt_packet(buffer, 0, PanDirection.LEFT, 24, TiltDirection.UP)

    @patch.object(RawViscaPacket, 'write_data', MagicMock(return_value=False))
    def test_create_pan_tilt_packet_Should_RaiseValueError_When_GivenTooSmallBuffer(self):
        buffer = bytearray(2)

        with self.assertRaises(RuntimeError):
            CameraAPI.create_pan_tilt_packet(buffer, 1, PanDirection.LEFT, 1, TiltDirection.UP)

    def test_create_pan_tilt_packet(self):
        pan_speeds = [1, 24, 20]
        tilt_speeds = [1, 23, 8]

        for pan_speed, tilt_speed, pan_direction, tilt_direction in product(pan_speeds, tilt_speeds, PanDirection, TiltDirection):
            buffer = bytearray(20)
            packet = CameraAPI.create_pan_tilt_packet(buffer, pan_speed, pan_direction, tilt_speed, tilt_direction)

            data = packet.data.tobytes()
            expected = bytearray(b'\x01\x06\x01')
            expected.append(pan_speed)
            expected.append(tilt_speed)
            expected.append(pan_direction)
            expected.append(tilt_direction)

            self.assertEqual(expected, data)


class TestCreateMemoryPacket(TestCase):

    def test_create_memory_packet_Should_RaiseValueError_When_GivenInvalidPositionIndex(self):
        buffer = bytearray(20)

        with self.assertRaises(ValueError):
            CameraAPI.create_memory_packet(buffer, -1, MemoryAction.RECALL)

        with self.assertRaises(ValueError):
            CameraAPI.create_memory_packet(buffer, 6, MemoryAction.RECALL)

    @patch.object(RawViscaPacket, 'write_data', MagicMock(return_value=False))
    def test_create_memory_packet_Should_RaiseValueError_When_GivenTooSmallBuffer(self):
        buffer = bytearray(3)

        with self.assertRaises(RuntimeError):
            CameraAPI.create_memory_packet(buffer, 5, MemoryAction.RECALL)

    def test_create_memory_packet(self):
        for position_index, memory_action in product(range(0, 6), MemoryAction):
            buffer = bytearray(20)
            packet = CameraAPI.create_memory_packet(buffer, position_index, memory_action)

            data = packet.data.tobytes()

            expected = bytearray(b'\x01\x04\x3f')
            expected.append(memory_action)
            expected.append(position_index)

            self.assertEqual(expected, data)


class TestCreateZoomPacket(TestCase):

    @patch.object(RawViscaPacket, 'write_data', MagicMock(return_value=False))
    def test_create_stop_zoom_packet_Should_RaiseRuntimeError_When_GivenTooSmallBuffer(self):
        buffer = bytearray(2)

        with self.assertRaises(RuntimeError):
            CameraAPI.create_stop_zoom_packet(buffer)

    def test_create_stop_zoom_packet(self):
        expected = b'\x01\x04\x07\x00'
        packet = CameraAPI.create_stop_zoom_packet(bytearray(10))

        self.assertEqual(expected, packet.data.tobytes())

    def test_create_zoom_packet_Should_RaiseValueError_When_GivenInvalidSpeed(self):
        buffer = bytearray(10)

        with self.assertRaises(ValueError):
            CameraAPI.create_zoom_packet(buffer, -1, ZoomDirection.WIDE)

        with self.assertRaises(ValueError):
            CameraAPI.create_zoom_packet(buffer, 8, ZoomDirection.WIDE)

    @patch.object(RawViscaPacket, 'write_data', MagicMock(return_value=False))
    def test_create_zoom_packet_Should_RaiseRuntimeError_When_GivenTooSmallBuffer(self):
        buffer = bytearray(10)

        with self.assertRaises(RuntimeError):
            CameraAPI.create_zoom_packet(buffer, 3, ZoomDirection.WIDE)

    def test_create_zoom_packet(self):
        speeds = [0, 3, 7]

        for zoom_speed, zoom_direction in product(speeds, ZoomDirection):
            packet = CameraAPI.create_zoom_packet(bytearray(10), zoom_speed, zoom_direction)

            data = packet.data.tobytes()
            expected = bytearray(b'\x01\x04\x07')
            expected.append(zoom_direction << 4 | zoom_speed)

            self.assertEqual(expected, data)
