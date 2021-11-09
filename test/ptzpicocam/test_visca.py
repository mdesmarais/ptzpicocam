import unittest
from io import BytesIO

from ptzpicocam.visca import RawViscaPacket


class TestRawViscaPacket(unittest.TestCase):

    def test_decode_When_GivenEmptyBody(self):
        data = BytesIO(b'\x81\xff')
        buffer = bytearray(10)

        packet = RawViscaPacket.decode(buffer, data)

        self.assertIsNotNone(packet)

        self.assertEqual(1, packet.receiver_addr)
        self.assertEqual(0, packet.sender_addr)
        self.assertEqual(0, packet.data_size)
        self.assertEqual(0, len(packet.data))

    def test_decode_When_GivenNonEmptyBody(self):
        data = BytesIO(b'\x81\x01\x02\xff')
        buffer = bytearray(10)

        packet = RawViscaPacket.decode(buffer, data)

        self.assertIsNotNone(packet)
        self.assertEqual(1, packet.receiver_addr)
        self.assertEqual(0, packet.sender_addr)
        self.assertEqual(2, packet.data_size)
        self.assertEqual(b'\x01\x02', packet.data.tobytes())

    def test_encode_When_GivenEmptyBody(self):
        packet = RawViscaPacket(1, 0, bytearray(2))
        result = packet.encode().tobytes()

        self.assertEqual(b'\x81\xff', result)

    def test_encode_When_GivenNonEmptyBody(self):
        packet = RawViscaPacket(1, 0, bytearray((0, 1, 2, 3, 0)))
        packet.data_size = 3
        result = packet.encode().tobytes()

        self.assertEqual(b'\x81\x01\x02\x03\xff', result)

    def test_write_data_Should_ReturnFalse_When_GivenTooSmallBuffer(self):
        buffer = bytearray(2)
        packet = RawViscaPacket(1, 0, buffer)

        self.assertFalse(packet.write_data(2))
        self.assertEqual(b'\x00\x00', buffer)

    def test_write_data(self):
        buffer = bytearray(4)
        packet = RawViscaPacket(1, 0, buffer)

        self.assertTrue(packet.write_data(2))
        self.assertEqual(b'\x00\x02\x00\x00', buffer)

        self.assertTrue(packet.write_data(4))
        self.assertEqual(b'\x00\x02\x04\x00', buffer)
