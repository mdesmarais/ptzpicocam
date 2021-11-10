import argparse
import os
import time
from threading import Thread

import pybullet as pb
from ptzpicocam.visca import RawViscaPacket
from serial import Serial, SerialException

from ptzsimcam.camera_server import SPEEDS_LOOKUP, process_packet
from ptzsimcam.robot_camera import RobotCamera


class Simulation:

    """A pybullet simulation for controlling a camera."""

    def __init__(self, camera: 'RobotCamera', enable_gui_control: bool = False):
        """Creates a new simulation into pybullet.
        
        :param camera: instance of the robot camera to control
        :param enable_gui_control: if True then the camera will be controlled with sliders
        """
        self.camera = camera
        self.enable_gui_control = enable_gui_control

        self.pan_vel_slider = pb.addUserDebugParameter('PAN vel', -0x18, 0x18, startValue=0)
        self.tilt_vel_slider = pb.addUserDebugParameter('TILT vel', -0x17, 0x17, startValue=0)
        self.zoom_vel_slider = pb.addUserDebugParameter('ZOOM vel', -7, 7, startValue=0)

    def gui_controller(self) -> None:
        """Reads slider values and sends driver packet to the camera.s"""
        pan_vel = pb.readUserDebugParameter(self.pan_vel_slider)
        tilt_vel = pb.readUserDebugParameter(self.tilt_vel_slider)
        zoom_vel = pb.readUserDebugParameter(self.zoom_vel_slider)

        if pan_vel < 0:
            pan_dir = 1
        elif pan_vel > 0:
            pan_dir = -1
        else:
            pan_dir = 0

        if tilt_vel < 0:
            tilt_dir = 1
        elif tilt_vel > 0:
            tilt_dir = -1
        else:
            tilt_dir = 0

        if zoom_vel < 0:
            zoom_dir = 1
        elif zoom_vel > 0:
            zoom_dir = -1
        else:
            zoom_dir = 0

        self.camera.pan_speed = SPEEDS_LOOKUP[abs(int(pan_vel))] * pan_dir
        self.camera.tilt_speed = SPEEDS_LOOKUP[abs(int(tilt_vel))] * tilt_dir
        self.camera.drive()

        self.camera.zoom_speed = abs(int(zoom_vel)) * zoom_dir

    def run(self):
        """Simulation loop."""
        frame_count = 0

        while True:
            if self.enable_gui_control:
                self.gui_controller()

            # By default the simulation runs at 240Hz
            # For the camera, 30Hz is enough. 240 / 30 = 8
            # We render an image every 8 frames.
            if frame_count == 8:
                self.camera.update(1.0/30)
                frame_count = 0

            pb.stepSimulation()
            frame_count += 1
            time.sleep(1.0/240)


def serial_control_thread(serial_port: str, camera: 'RobotCamera') -> None:
    """Reads packet from a serial port and sends them to the camera.

    This function is blocking, it should be executed in a dedicated thread.
    
    :param serial_port: a serial port for receiving packets
    :param camera: instance of the camera to control"""
    try:
        conn = Serial(serial_port)
    except SerialException:
        print(f'Unable to connect to {serial_port}')
        return

    buffer = bytearray(16)

    while True:
        p = RawViscaPacket.decode(buffer, conn)

        if p is None:
            continue

        process_packet(camera, p)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description='Simulation of the EVI-D100P Sony camera.')
    parser.add_argument('--serial', default=None, metavar='port', dest='serial_port', help='Path of a serial port for communicating with the camera')

    args = parser.parse_args()

    pb.connect(pb.GUI)

    # We need to call stepSimulation to make the simulation progressing
    pb.setRealTimeSimulation(0)

    # Disables non-necessary debug windows
    pb.configureDebugVisualizer(pb.COV_ENABLE_SEGMENTATION_MARK_PREVIEW,0)
    pb.configureDebugVisualizer(pb.COV_ENABLE_DEPTH_BUFFER_PREVIEW,0)

    # The flag URDF_USE_INERTIA_FROM_FILE is IMPORTANT
    # By default Bullet computes an approximation of the inertia matrix
    # without looking at the urdf. A better matrix can be computed by hand.
    current_foler = os.path.dirname(__file__)
    robot_camera = pb.loadURDF(os.path.join(current_foler, 'camera.urdf'), flags=pb.URDF_USE_INERTIA_FROM_FILE)
    pb.loadURDF(os.path.join(current_foler, 'wall.urdf'), basePosition=[0.0, 5.0, 0.5])
    pb.loadURDF(os.path.join(current_foler, 'wall_blue.urdf'), basePosition=[-5.0, 0.0, 0.5])

    camera = RobotCamera(robot_camera, 1, 2)
    serial_port = args.serial_port

    if not serial_port is None:
        serial_thread = Thread(target=serial_control_thread, args=(serial_port, camera))
        serial_thread.start()

    sim = Simulation(camera, enable_gui_control=serial_port is None)
    sim.run()
    pb.disconnect()

if __name__ == '__main__':
    main()
