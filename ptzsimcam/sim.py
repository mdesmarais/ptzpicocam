import argparse
import os
import time
from threading import Thread

import pybullet as pb
from serial import Serial, SerialException

from camera_server import handle_pan_tilt_packet, process_packet
from robot_camera import RobotCamera
from visca import RawViscaPacket


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

    def gui_controller(self) -> None:
        """Reads slider values and sends driver packet to the camera.s"""
        pan_vel = pb.readUserDebugParameter(self.pan_vel_slider)
        tilt_vel = pb.readUserDebugParameter(self.tilt_vel_slider)

        if pan_vel < 0:
            pan_dir = 1
        elif pan_vel > 0:
            pan_dir = 2
        else:
            pan_dir = 3

        if tilt_vel < 0:
            tilt_dir = 1
        elif tilt_vel > 0:
            tilt_dir = 2
        else:
            tilt_dir = 3

        data = bytearray(b'\x01\x06\x01')
        data.append(abs(int(pan_vel)))
        data.append(abs(int(tilt_vel)))
        data.append(pan_dir)
        data.append(tilt_dir)

        p = RawViscaPacket(1, 0, data)
        handle_pan_tilt_packet(self.camera, p)

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
                self.camera.render_image()
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

    while True:
        process_packet(camera, RawViscaPacket.decode(conn))


def main(args) -> None:
    """Main function."""
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
    pb.loadURDF(os.path.join(current_foler, 'wall.urdf'), basePosition=[0.0, 2.0, 0.5])

    camera = RobotCamera(robot_camera, 1, 2)
    serial_port = args.serial_port

    if not serial_port is None:
        serial_thread = Thread(target=serial_control_thread, args=(serial_port, camera))
        serial_thread.start()

    sim = Simulation(camera, enable_gui_control=serial_port is None)
    sim.run()
    pb.disconnect()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simulation of the EVI-D100P Sony camera.')
    parser.add_argument('--serial', default=None, metavar='port', dest='serial_port', help='Path of a serial port for communicating with the camera')

    main(parser.parse_args())
