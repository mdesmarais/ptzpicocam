import unittest
from io import BytesIO

from ptzpicocam.visca import RawViscaPacket


class TestRawViscaPacket(unittest.TestCase):

    def test_decode_When_GivenEmptyBody(self):
        data = BytesIO(b'\x81\xff')
        packet = RawViscaPacket.decode(data)

        self.assertIsNotNone(packet)

        self.assertEqual(1, packet.receiver_addr)
        self.assertEqual(0, packet.sender_addr)
        self.assertEqual(0, len(packet.raw_data))

    def test_decode_When_GivenNonEmptyBody(self):
        data = BytesIO(b'\x81\x01\x02\xff')
        packet = RawViscaPacket.decode(data)

        self.assertIsNotNone(packet)
        self.assertEqual(1, packet.receiver_addr)
        self.assertEqual(0, packet.sender_addr)
        self.assertEqual(b'\x01\x02', bytes(packet.raw_data))

    def test_encode_When_GivenEmptyBody(self):
        packet = RawViscaPacket(1, 0, bytearray())
        result = packet.encode()

        self.assertEqual(b'\x81\xff', result)

    def test_encode_When_GivenNonEmptyBody(self):
        packet = RawViscaPacket(1, 0, bytearray((1, 2, 3)))
        result = packet.encode()

        self.assertEqual(b'\x81\x01\x02\x03\xff', result)
