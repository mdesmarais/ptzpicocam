import logging
from typing import Callable, Dict, List

from robot_camera import RobotCamera
from visca import RawViscaPacket

# Association between a speed value (from 1 to 0x18, it is an index) to a
# speed in degrees/s
SPEEDS_LOOKUP: List[float] = [0,
    1.3, 1.7, 2.2, 3.2, 5.4, 11, 16, 21,
    27, 31, 35, 40, 42, 44, 46, 48,
    50, 79, 81, 83, 85, 87, 90, 100
]

logger = logging.getLogger(__name__)


def handle_memory_packet(camera: 'RobotCamera', packet: 'RawViscaPacket'):
    """Saves, restores, resets memory points according to the given packet.
    
    The packet should be a Memory command.
    If the command is set or recall then the position index must
    be a number between 0 and 5 included, otherwise the packet
    will be ignored.
    
    :param camera: instance of the camera to update
    :param packet: a packet containing a Memory command"""
    if len(packet.raw_data) != 5:
        logger.warning(f'Invalid memory packet, expected size of 5, got {len(packet.raw_data)}')
        return

    action = packet.raw_data[3]
    position_index = packet.raw_data[4]

    if position_index < 0 or position_index > 5:
        logger.warning(f'Invalid position index {position_index}')
        return

    if action == 0:
        camera.reset_positions()
    elif action == 1:
        camera.set_position(position_index)
    elif action == 2:
        camera.recall_position(position_index)
    else:
        logger.warning(f'Unknown memory command {action}')


def handle_pan_tilt_packet(camera: 'RobotCamera', packet: 'RawViscaPacket'):
    """Updates camera direction speeds according to the given packet.
    
    The packet should be a PanTiltDrive command.
    If it is not valid then it will be ignored.
    If it contains a non valid speed then pan and tilt speed will be set to 0.
    
    :param camera: instance of the camera to update
    :param packet: a packet containing a PanTiltDrive command"""
    if len(packet.raw_data) != 7:
        logger.warning(f'Invalid pan tilt packet, expected size of 7, got {len(packet.raw_data)}')
        return

    try:
        pan_speed = SPEEDS_LOOKUP[packet.raw_data[3]]
        tilt_speed = SPEEDS_LOOKUP[packet.raw_data[4]]
    except IndexError:
        pan_speed = 0
        tilt_speed = 0

    pan_direction = packet.raw_data[5]
    tilt_direction = packet.raw_data[6]

    if pan_direction == 1:
        camera.pan_speed = pan_speed
    elif pan_direction == 2:
        camera.pan_speed = -pan_speed
    else:
        camera.pan_speed = 0

    if tilt_direction == 1:
        camera.tilt_speed  = tilt_speed
    elif tilt_direction == 2:
        camera.tilt_speed = -tilt_speed
    else:
        camera.tilt_speed = 0

    camera.drive()


def process_packet(camera: 'RobotCamera', packet: 'RawViscaPacket') -> None:
    """Calls the corresponding handler for the given packet.
    
    If the packet has an unknown signature then it will be ignored.
    
    :param camera: instance of the camera to update
    :param packet: packet to handle
    """
    for packet_signature, packet_handler in PACKET_SIGNATURES.items():
        if packet.raw_data.startswith(packet_signature):
            packet_handler(camera, packet)
            return

    logger.warning(f'Unknown packet {packet.raw_data}')


# Association between the start of a packet with a handler
PACKET_SIGNATURES: Dict[bytes, Callable[['RobotCamera', 'RawViscaPacket'], None]] = {
    b'\x01\x04\x3f': handle_memory_packet,
    b'\x01\x06\x01': handle_pan_tilt_packet
}
