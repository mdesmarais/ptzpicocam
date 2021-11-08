from typing import BinaryIO, Optional


class RawViscaPacket:

    """Represents a raw packet used in the Visca protocol.
    
    A packet contains a header, a body and a terminator byte (0xff).
    The header contains two addresses : the receiver and the sender.
    The body has a variable length."""

    def __init__(self, receiver_addr: int, sender_addr: int, buffer: bytearray):
        """Creates a new raw packet.

        The buffer must have a capacity of at least 2 bytes.
        
        :param receiver_addr: address of the receiver
        :param sender_addr: address of the sender
        :param buffer: a buffer for holding the packet
        """
        self.receiver_addr = receiver_addr
        self.sender_addr = sender_addr
        self.buffer = buffer
        self.buffer_view = memoryview(buffer)
        self.data_size = 0

    def encode(self) -> memoryview:
        """Writes headers and terminating byte into the buffer and returns it."""
        self.buffer[0] = (1<<7) | ((self.sender_addr & 0x7) << 4) | (self.receiver_addr & 0x7)
        self.buffer[1 + self.data_size] = 0xff

        return self.buffer_view[:self.data_size + 2]

    @property
    def data(self) -> memoryview:
        """Gets a pointer on the buffer containing the packet data."""
        return self.buffer_view[1:1 + self.data_size]

    @classmethod
    def decode(cls, buffer: bytearray, stream: BinaryIO) -> Optional['RawViscaPacket']:
        """Decodes a packet from the given stream.
        
        The stream must be readable and contain at least 2 bytes (header + terminator).
        The given buffer must be large enough for holding the entire packet. If it is not
        the case then the method will return None.

        :param buffer: a buffer for holding the packet
        :param stream: stream of bytes
        :return: a new instance of :py:class:`~.RawViscaPacket` representing the packet or None if the buffer is too small
        """
        header = stream.read(1)[0]

        receiver_addr = header & 0x7
        sender_addr = (header >> 4) & 0x7

        packet = RawViscaPacket(receiver_addr, sender_addr, buffer)

        i = 0

        while True:
            data = stream.read(1)[0]

            if data == 0xff:
                break

            if not packet.write_data(data):
                return None

            i += 1

        return packet

    def write_data(self, b: int) -> bool:
        """Writes a byte in the buffer at the next available position.
        
        If the buffer is full then it will return False.
        
        :param b: a byte to write
        :returns: True if the byte has be written in the buffer, otherwise False
        """
        if len(self.buffer) - 2 <= self.data_size:
            return False

        self.buffer[1 + self.data_size] = b & 0xff
        self.data_size += 1

        return True

    def write_bytes(self, data: bytes) -> bool:
        """Writes bytes in the buffer at the next available position.
        
        If the buffer is full then it will return False.
        
        :param b: a byte to write
        :returns: True if all bytes have be written in the buffer, otherwise False
        """
        for b in data:
            if not self.write_data(b):
                return False

        return True
