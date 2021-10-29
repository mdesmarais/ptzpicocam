from enum import IntEnum

class CameraAPI:

    """API for controlling a camera with the VISCA protocol."""

    class PanDirection(IntEnum):

        """Represents a direction for the pan (X axe)."""

        LEFT = 1
        RIGHT = 2

    class TiltDirection(IntEnum):

        """Represents a direction for the tilt (Y axe)."""

        UP = 1
        DOWN = 2

    class ZoomDirection(IntEnum):

        """Represents a direction for the camera zoom.
        
        TELE = FORWARD
        WIDE = BACKWARD"""

        TELE = 2
        WIDE = 3


    def setTiltPan(self, tilt_direction: 'TiltDirection', tilt_speed: int, pan_direction: 'PanDirection', pan_speed: int) -> None:
        """Moves the camera around two axes (pan / title).

        If the speed is 0 then the camera will not move on
        the associated axe anymore.

        :param tilt_direction: a direction around the Y axe
        :param tilt_speed: a speed value between 0 and 23
        :param pan_direction: a direction around the X axe
        :param pan_speed: a speed value between 0 and 24
        :raises ValueError: if any of the given speed is not in the expected range
        """
        pass

    def setZoom(self, zoom_speed: int, direction: 'ZoomDirection') -> None:
        """Sets a zoom speed in the given direction.

        :param zoom_speed: a speed value between 0 and 7
        :param direction: a direction
        :raises ValueError: if zoom_speed is not between 0 and 7 included"""
        pass

    def stopZoom(self) -> None:
        """Stops the camera from zooming."""
        pass

