from enum import IntEnum

from ptzpicocam.visca import RawViscaPacket


class CameraAPI:

    """API for controlling a camera with the VISCA protocol."""

    @classmethod
    def create_pan_tilt_packet(cls, buffer: bytearray, pan_speed: int, pan_direction: 'PanDirection', tilt_speed: int, tilt_direction: 'TiltDirection') -> None:
        """Moves the camera around two axes (pan / title).

        The buffer must have a capacity of at least 7 bytes.
        Pan speed must be a value between 1 and 24.
        Tilt speed must be a value between 1 and 23.
        If any of the previous conditions is not met then
        a ValueError exception will be raised.

        :param buffer: a buffer for holding the packet
        :param pan_direction: a direction around the X axe
        :param pan_speed: a speed value between 0 and 24
        :param tilt_speed: a speed value between 0 and 23
        :param tilt_direction: a direction around the Y axe
        :raises ValueError: if a speed is not valid or the buffer is too small
        """
        if len(buffer) < 7:
            raise ValueError('The buffer must have a capacity of at least 7 bytes')

        if pan_speed < 1 or pan_speed > 24:
            raise ValueError('Pan speed must be a value between 1 and 24')

        if tilt_speed < 1 or tilt_speed > 24:
            raise ValueError('Tilt speed must be a value between 1 and 23')

        packet = RawViscaPacket(1, 0, buffer)
        packet.write_bytes(b'\x01\x06\x01')
        packet.write_data(pan_speed & 0xff)
        packet.write_data(tilt_speed & 0xff)
        packet.write_data(pan_direction & 0xff)
        packet.write_data(tilt_direction & 0xff)

        return packet

    @classmethod
    def create_stop_zoom_packet(cls, buffer: bytearray) -> None:
        """Stops the camera from zooming."""
        pass

    @classmethod
    def create_zoom_packet(cls, buffer: bytearray, zoom_speed: int, direction: 'ZoomDirection') -> None:
        """Sets a zoom speed in the given direction.

        :param zoom_speed: a speed value between 0 and 7
        :param direction: a direction
        :raises ValueError: if zoom_speed is not between 0 and 7 included"""
        pass


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

    TELE = 2
    WIDE = 3
