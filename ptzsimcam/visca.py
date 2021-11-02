from typing import BinaryIO, Optional


class RawViscaPacket:

    """Represents a raw packet used in the Visca protocol.
    
    A packet contains a header, a body and a terminator byte (0xff).
    The header contains two addresses : the receiver and the sender.
    The body has a variable length."""

    def __init__(self, receiver_addr: int, sender_addr: int, raw_data: bytearray):
        """Creates a new raw packet.
        
        :param receiver_addr: address of the receiver
        :param sender_addr: address of the sender
        :param raw_data: packet data as a bytearray"""
        self.receiver_addr = receiver_addr
        self.sender_addr = sender_addr
        self.raw_data = raw_data

    @classmethod
    def decode(cls, stream: BinaryIO) -> Optional['RawViscaPacket']:
        """Decodes a packet from the given stream.
        
        The stream must be readable and contain at least 2 bytes (header + terminator).
        
        :param stream: stream of bytes
        :return: a new instance of :py:class:`~.RawViscaPacket` representing the packet"""
        header = int.from_bytes(stream.read(1), 'little')

        receiver_addr = header & 0x7
        sender_addr = (header >> 4) & 0x7

        packet_data = bytearray()

        while True:
            data = stream.read(1)

            if int.from_bytes(data, 'little') == 0xff:
                break

            packet_data += data

        return RawViscaPacket(receiver_addr, sender_addr, packet_data)

    def encode(self) -> bytes:
        """Encodes the packet into bytes.
        
        :return: bytes representing the packet"""
        header = (1<<7) | ((self.sender_addr & 0x7) << 4) | (self.receiver_addr & 0x7)

        return int.to_bytes(header, 1, 'little') + bytes(self.raw_data) + b'\xff'
