"""Defines API for creating VISCA packets and enumerations."""
try:
    from enum import IntEnum
except ImportError:
    from uenum import IntEnum

from ptzpicocam.visca import RawViscaPacket


class CameraAPI:

    """API for controlling a camera with the VISCA protocol."""

    @classmethod
    def create_pan_tilt_packet(cls, buffer: bytearray, pan_speed: int, pan_direction: 'PanDirection', tilt_speed: int, tilt_direction: 'TiltDirection') -> 'RawViscaPacket':
        """Creates a packet for moving the camera around two axes (pan / title).

        The given buffer must have a capacity of at least 7 bytes. It will
        raise a RuntimeError if the buffer is too small. It could have been
        modified even if an exception is thrown.

        Pan speed must be a value between 1 and 24.
        Tilt speed must be a value between 1 and 23.
        If any of the previous conditions is not met then
        a ValueError exception will be raised.

        :param buffer: a buffer for holding the packet
        :param pan_direction: a direction around the X axe
        :param pan_speed: a speed value between 0 and 24
        :param tilt_speed: a speed value between 0 and 23
        :param tilt_direction: a direction around the Y axe
        :raises RuntimeError: if the buffer is too small
        :raises ValueError: if a speed is not valid or the buffer is too small
        :returns: a packet containing a drive command
        """
        if pan_speed < 1 or pan_speed > 24:
            raise ValueError('Pan speed must be a value between 1 and 24')

        if tilt_speed < 1 or tilt_speed > 24:
            raise ValueError('Tilt speed must be a value between 1 and 23')

        packet = RawViscaPacket(1, 0, buffer)
        result = packet.write_bytes(b'\x01\x06\x01')
        result |= packet.write_data(pan_speed)
        result |= packet.write_data(tilt_speed)
        result |= packet.write_data(pan_direction)
        result |= packet.write_data(tilt_direction)

        if not result:
            raise RuntimeError('The buffer requires at least 7 bytes')

        return packet

    @classmethod
    def create_memory_packet(cls, buffer: bytearray, position_index: int, memory_action: 'MemoryAction') -> 'RawViscaPacket':
        """Creates a packet for interacting with the camera positions memory.

        The given buffer must have a capacity of at least 5 bytes. It will
        raise a RuntimeError if the buffer is too small. It could have been
        modified even if an exception is thrown.

        The camera supports 6 positions : a position must be called by its index.
        It is an integer between 0 and 5 included.

        :param buffer: a buffer for holding the packet
        :param position_index: index of the position to select (0-5)
        :param memory_action: action to perform on the selected position
        :raises RuntimeError: if the buffer is too small
        :raises ValueError: if the index is not valid
        :returns: a memory packet
        """
        if position_index < 0 or position_index > 5:
            raise ValueError('Position index must be a value between 0 and 5 included')

        packet = RawViscaPacket(1, 0, buffer)
        result = packet.write_bytes(b'\x01\x04\x3f')
        result |= packet.write_data(memory_action)
        result |= packet.write_data(position_index)

        if not result:
            raise RuntimeError('The buffer requires at least 5 bytes')

        return packet

    @classmethod
    def create_recall_position_packet(cls, buffer: bytearray, position_index: int) -> 'RawViscaPacket':
        """Creates a packet for recalling a position.

        It is an alias of :py:meth:`~.CameraAPI.create_memory_packet`. 
        """
        return cls.create_memory_packet(buffer, position_index, MemoryAction.RECALL)

    @classmethod
    def create_reset_position_packet(cls, buffer: bytearray, position_index: int) -> 'RawViscaPacket':
        """Creates a packet for resetting a position.

        It is an alias of :py:meth:`~.CameraAPI.create_memory_packet`. 
        """
        return cls.create_memory_packet(buffer, position_index, MemoryAction.RESET)

    @classmethod
    def create_set_position_packet(cls, buffer: bytearray, position_index: int) -> 'RawViscaPacket':
        """Creates a packet for setting a position.

        It is an alias of :py:meth:`~.CameraAPI.create_memory_packet`. 
        """
        return cls.create_memory_packet(buffer, position_index, MemoryAction.SET)

    @classmethod
    def create_stop_zoom_packet(cls, buffer: bytearray) -> 'RawViscaPacket':
        """Creates a packet for stopping the camera zoom..

        The given buffer must have a capacity of at least 4 bytes. It will
        raise a RuntimeError if the buffer is too small. It could have been
        modified even if an exception is thrown.

        :raises RuntimeError: if the buffer is too small
        :returns: a packet containing a stop zoom command
        """
        packet = RawViscaPacket(1, 0, buffer)
        result = packet.write_bytes(b'\x01\x04\x07\x00')

        if not result:
            raise RuntimeError('The buffer must have a capacity of at least 4 bytes')

        return packet

    @classmethod
    def create_zoom_packet(cls, buffer: bytearray, zoom_speed: int, direction: 'ZoomDirection') -> 'RawViscaPacket':
        """Creates a packet for controlling the camera zoom.

        The given buffer must have a capacity of at least 4 bytes. It will
        raise a RuntimeError if the buffer is too small. It could have been
        modified even if an exception is thrown.

        :param zoom_speed: a speed value between 0 and 7
        :param direction: a direction
        :raises RuntimeError: if the buffer is too small
        :raises ValueError: if zoom_speed is not between 0 and 7 included
        :returns: a packet containing a zoom command
        """
        if zoom_speed < 0 or zoom_speed > 7:
            raise ValueError('Zoom speed must be a value between 0 and 7 included')

        packet = RawViscaPacket(1, 0, buffer)
        result = packet.write_bytes(b'\x01\x04\x07')
        result |= packet.write_data(direction << 4 | zoom_speed)

        if not result:
            raise RuntimeError('The buffer must have a capacity of at least 4 bytes')

        return packet


class MemoryAction(IntEnum):

    """Available actions when interacting with camera positions memory."""

    RESET = 0
    SET = 1
    RECALL = 2
    NONE = 3

class PanDirection(IntEnum):

    """Represents a direction for the pan (X axe)."""

    LEFT = 1
    RIGHT = 2
    NONE = 3

class TiltDirection(IntEnum):

    """Represents a direction for the tilt (Y axe)."""

    UP = 1
    DOWN = 2
    NONE = 3

class ZoomDirection(IntEnum):

    """Represents a direction for the camera zoom.
    
    TELE = FORWARD
    WIDE = BACKWARD"""

    NONE = 0
    TELE = 2
    WIDE = 3
