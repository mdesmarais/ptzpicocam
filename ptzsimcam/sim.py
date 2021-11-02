import pybullet as pb

from camera import Camera, handle_pan_tilt_packet
from visca import RawViscaPacket


class Simulation:

    def __init__(self, camera: 'Camera', debug: bool = False):
        self.camera = camera
        self.debug = debug

        #self.pan_slider = pb.addUserDebugParameter('PAN', -100, 100, startValue=0)
        self.pan_vel_slider = pb.addUserDebugParameter('PAN vel', -0x18, 0x18, startValue=0)

        #self.tilt_slider = pb.addUserDebugParameter('TILT', -25, 25, startValue=0)
        self.tilt_vel_slider = pb.addUserDebugParameter('TILT vel', -0x17, 0x17, startValue=0)

    def run(self):
        while True:
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

if __name__ == '__main__':
    physicsClient = pb.connect(pb.GUI)
    pb.setRealTimeSimulation(1)

    # The flag URDF_USE_INERTIA_FROM_FILE is IMPORTANT
    # By default Bullet computes an approximation of the inertia matrix
    # without looking at the urdf. A better matrix can be computed by hand.
    robot_camera = pb.loadURDF('camera.urdf', flags=pb.URDF_USE_INERTIA_FROM_FILE)

    camera = Camera(robot_camera, 1, 2)
    sim = Simulation(camera)
    sim.run()
    pb.disconnect()
