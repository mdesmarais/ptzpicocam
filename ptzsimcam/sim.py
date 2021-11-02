import time

import pybullet as pb

from camera_server import handle_pan_tilt_packet
from robot_camera import RobotCamera
from visca import RawViscaPacket


class Simulation:

    """A pybullet simulation for controlling a camera."""

    def __init__(self, camera: 'RobotCamera'):
        """Creates a new simulation into pybullet.
        
        :param camera: instance of the robot camera to control
        """
        self.camera = camera

        #self.pan_slider = pb.addUserDebugParameter('PAN', -100, 100, startValue=0)
        self.pan_vel_slider = pb.addUserDebugParameter('PAN vel', -0x18, 0x18, startValue=0)

        #self.tilt_slider = pb.addUserDebugParameter('TILT', -25, 25, startValue=0)
        self.tilt_vel_slider = pb.addUserDebugParameter('TILT vel', -0x17, 0x17, startValue=0)

    def run(self):
        """Simulation loop."""
        frame_count = 0

        while True:
            # Test code start
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
            # Test code end

            # By default the simulation runs at 240Hz
            # For the camera, 30Hz is enough. 240 / 30 = 8
            # We render an image every 8 frames.
            if frame_count == 8:
                self.camera.render_image()
                frame_count = 0

            pb.stepSimulation()
            frame_count += 1
            time.sleep(1.0/240)

if __name__ == '__main__':
    physicsClient = pb.connect(pb.GUI)

    # We need to call stepSimulation to make the simulation progressing
    pb.setRealTimeSimulation(0)

    # Disables non-necessary debug windows
    pb.configureDebugVisualizer(pb.COV_ENABLE_SEGMENTATION_MARK_PREVIEW,0)
    pb.configureDebugVisualizer(pb.COV_ENABLE_DEPTH_BUFFER_PREVIEW,0)

    # The flag URDF_USE_INERTIA_FROM_FILE is IMPORTANT
    # By default Bullet computes an approximation of the inertia matrix
    # without looking at the urdf. A better matrix can be computed by hand.
    robot_camera = pb.loadURDF('camera.urdf', flags=pb.URDF_USE_INERTIA_FROM_FILE)
    pb.loadURDF('wall.urdf', basePosition=[0.0, 2.0, 0.5])

    camera = RobotCamera(robot_camera, 1, 2)
    sim = Simulation(camera)
    sim.run()
    pb.disconnect()
