"""Defines functions for handling incoming VISCA packets."""
import logging
from queue import Empty, Queue
from threading import Thread
from typing import Callable, Dict, List

from ptzpicocam.visca import RawViscaPacket
from serial import Serial, SerialException

from ptzsimcam.robot_camera import RobotCamera

SPEEDS_LOOKUP: List[float] = [0,
    1.3, 1.7, 2.2, 3.2, 5.4, 11, 16, 21,
    27, 31, 35, 40, 42, 44, 46, 48,
    50, 79, 81, 83, 85, 87, 90, 100
]
"""Association between a speed value (from 1 to 0x18, it is an index) to a speed in degrees/s."""

logger = logging.getLogger(__name__)


def serial_control_thread(serial_port: str, packets_queue: "Queue[RawViscaPacket]") -> None:
    """Reads packet from a serial port and sends it to the pakets queue.

    This function is blocking, it should be executed in a dedicated thread.
    
    :param serial_port: a serial port for receiving packets
    :param packets_queue: queue of packes that will be processed by the camera
    """
    try:
        conn = Serial(serial_port)
    except SerialException:
        logger.error(f'Unable to connect to {serial_port}')
        return

    while True:
        p = RawViscaPacket.decode(bytearray(16), conn)

        if not p is None:
            packets_queue.put(p, block=True, timeout=None)


class CameraServer:

    """Receives and processes packets from a serial port."""

    def __init__(self, camera: 'RobotCamera'):
        self.camera = camera
        self.packets_queue: "Queue[RawViscaPacket]" = Queue(2)
        self.started = False

    def process_incoming_packet(self) -> None:
        """Processes the first packet in the queue (if not empty).
        
        If the camera is busy then the method does nothing.
        It should be called periodically.
        """
        if self.camera.is_busy:
            return

        try:
            packet = self.packets_queue.get(block=False)
        except Empty:
            pass
        else:
            process_packet(self.camera, packet)

    def start_receiver_thread(self, serial_port: str) -> None:
        """Starts a new thread for receiving packets.
        
        The attriute :py:attr:`~.CameraServer.started` will be set to True.
        """
        self.started = True
        receiver_thread = Thread(target=serial_control_thread, args=(serial_port, self.packets_queue))
        receiver_thread.start()


def handle_memory_packet(camera: 'RobotCamera', packet: 'RawViscaPacket') -> bool:
    """Saves, restores, resets memory points according to the given packet.
    
    The packet should be a Memory command.
    If the command is set or recall then the memory index must
    be a number between 0 and 5 included, otherwise the packet
    will be ignored. Reset action is not implemented.
    
    :param camera: instance of the camera to update
    :param packet: a packet containing a Memory command
    """
    packet_data = packet.data
    if len(packet_data) != 5:
        logger.warning(f'Invalid memory packet, expected size of 5, got {len(packet_data)}')
        return False

    action = packet_data[3]
    memory_index = packet_data[4]

    if memory_index < 0 or memory_index > 5:
        logger.warning(f'Invalid memory index {memory_index}')
        return False

    if action == 0:
        logger.warning('Reset memory command is not implemented yet')
    elif action == 1:
        camera.set_memory(memory_index)
    elif action == 2:
        camera.recall_memory(memory_index)
    else:
        logger.warning(f'Unknown memory command {action}')
        return False

    return True


def handle_pan_tilt_packet(camera: 'RobotCamera', packet: 'RawViscaPacket') -> bool:
    """Updates camera direction speeds according to the given packet.
    
    The packet should be a PanTiltDrive command.
    If it is not valid then the method will reuurn False.
    If it contains a non valid speed then pan and tilt speed will be set to 0.
    
    :param camera: instance of the camera to update
    :param packet: a packet containing a PanTiltDrive command"""
    packet_data = packet.data
    if len(packet_data) != 7:
        logger.warning(f'Invalid pan tilt packet, expected size of 7, got {len(packet_data)}')
        return False

    try:
        pan_speed = SPEEDS_LOOKUP[packet_data[3]]
        tilt_speed = SPEEDS_LOOKUP[packet_data[4]]
    except IndexError:
        pan_speed = 0
        tilt_speed = 0

    pan_direction = packet_data[5]
    tilt_direction = packet_data[6]

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

    return True


def handle_zoom_packet(camera: 'RobotCamera', packet: 'RawViscaPacket') -> bool:
    """Updates the camera zoom according to the given packet.
    
    The packet should be a Zoom command.
    If the packet contains an invalid zoom speed then it will be ignored,
    or if the direction is unknown.
    
    :param camera: instance of the camera to update
    :param packet: a packet containing a Zoom command"""
    packet_data = packet.data
    if len(packet_data) != 4:
        logger.warning(f'Invalid zoom packet, expected size of 4, got {len(packet_data)}')
        return False

    zoom_data = packet_data[3]
    direction = (zoom_data >> 4) & 0xf
    speed = zoom_data & 0xf

    if speed < 1 or speed > 7:
        logger.warning(f'Expecting zoom speed between 1 and 7, got {speed}')
        return False

    if direction == 0:
        camera.zoom_speed = 0
    elif direction == 2:
        camera.zoom_speed = -speed
    elif direction == 3:
        camera.zoom_speed = speed
    else:
        logger.warning(f'Unknown zoom direction {direction}')
        return False

    return True


def process_packet(camera: 'RobotCamera', packet: 'RawViscaPacket') -> None:
    """Calls the corresponding handler for the given packet.
    
    If the packet has an unknown signature then it will be ignored.
    
    :param camera: instance of the camera to update
    :param packet: packet to handle
    """
    packet_data = packet.data.tobytes()
    for packet_signature, packet_handler in PACKET_SIGNATURES.items():
        if packet_data.startswith(packet_signature):
            packet_handler(camera, packet)
            return

    logger.warning(f'Unknown packet {packet_data}')


PACKET_SIGNATURES: Dict[bytes, Callable[['RobotCamera', 'RawViscaPacket'], bool]] = {
    b'\x01\x04\x3f': handle_memory_packet,
    b'\x01\x06\x01': handle_pan_tilt_packet,
    b'\x01\x04\x07': handle_zoom_packet
}
"""Association between the start of a packet with a handler"""
