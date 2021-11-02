import pybullet as pb

from camera import Camera


class Simulation:

    def __init__(self, camera: 'Camera', debug: bool = False):
        self.camera = camera
        self.debug = debug

        """self.pan_slider = pb.addUserDebugParameter('PAN', -100, 100, startValue=0)
        self.pan_vel_slider = pb.addUserDebugParameter('PAN vel', -0x18, 0x18, startValue=0)

        self.tilt_slider = pb.addUserDebugParameter('TILT', -25, 25, startValue=0)
        self.tilt_vel_slider = pb.addUserDebugParameter('TILT vel', -0x17, 0x17, startValue=0)"""

    def run(self):
        while True:
            pass

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
