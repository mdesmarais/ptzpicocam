"""Defines a camera robot based on the EVI-D100 by Sony for pybullet."""
import math
from typing import cast

import numpy as np
import pybullet as pb
from scipy.spatial.transform import Rotation as R

from ptzsimcam.homogeneous_transform import rot_x, rot_z, translation

ZOOM_SPEEDS = [0, 1, 2, 5, 7, 10, 15, 20]
"""Association between a visca zoom speed (0, 7) and a zoom speed in degrees/s."""

class RobotCamera:

    """Represents a camera that uses the VISCA protocol."""

    ZOOM_FOV_MIN = 2.9
    ZOOM_FOV_MAX = 55.9

    def __init__(self, main_link, pan_joint_index: int, tilt_joint_index: int):
        """Creates a new robot camera in a simulation.
        
        A robot camera is made of 2 joints.
        
        :param main_link: root link in the associated urdf
        :param pan_joint_index: index of the first joint
        :param tilt_joint_index: index of the second joint
        """
        self.main_link = main_link
        self.joints = [pan_joint_index, tilt_joint_index]

        self.camera_direction = np.array([0.0, 10.0, 0.0])
        self.camera_orientation = np.array([0.0, 0.0, 1.0])
        self.projection_matrix = compute_projection_matrix(self.ZOOM_FOV_MAX)
        self.current_fov = self.ZOOM_FOV_MAX

        self.first_join_base = translation(np.array([0.0, 0.25, 0.15]))
        self.second_join_base = translation(np.array([0.0, 0.1, 0.4]))
        self.camera_end = translation(np.array([0.0, 0.9/2, 0.0]))

        self.pan_speed = 0.0
        self.tilt_speed = 0.0
        self.zoom_speed = 0

        # Recorded positions, 6 available
        self.positions = [
            [0.0, 0.0], [0.0, 0.0], [0.0, 0.0],
            [0.0, 0.0], [0.0, 0.0], [0.0, 0.0],
            [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]
        ]

    def drive(self) -> None:
        """Moves the camera with the current pan and tilt speeds."""
        pb.setJointMotorControlArray(
            self.main_link, self.joints,
            pb.VELOCITY_CONTROL, targetVelocities=[math.radians(self.pan_speed), math.radians(self.tilt_speed)], 
            forces=[0.2, 0.2], velocityGains=[0.01, 0.01]
        )

    def get_base_from_camera(self) -> np.ndarray:
        """Gets the base position at the end of the robot."""
        joint_states = [x[0] for x in pb.getJointStates(self.main_link, self.joints)]

        return self.first_join_base.dot(
            rot_z(joint_states[0])).dot(self.second_join_base).dot(
                rot_x(joint_states[1])).dot(self.camera_end)

    def recall_position(self, position_index: int) -> None:
        """Moves the camera to the position recorded at the given index.
        
        :param position_index: index of the position to recall
        :raises ValueError: if the index is not between 0 and 5 included
        """
        if position_index < 0 or position_index > 5:
            raise ValueError('Invalid position index, must be between 0 and 5 included')

        pb.setJointMotorControlArray(
            self.main_link, self.joints, 
            pb.POSITION_CONTROL, targetPositions=self.positions[position_index],
            forces=[0.3, 0.3], positionGains=[0.01, 0.01]
        )

    def render_image(self):
        """Renders an image using the simulated camera of pybullet.
        
        The camera will be placed at the end of the robot.
        """
        world_from_tool = self.get_base_from_camera()
        tool_pos = world_from_tool[:3, 3]

        direction = R.from_matrix(world_from_tool[:3, :3]).apply(self.camera_direction)
        view_matrix = pb.computeViewMatrix(tool_pos, direction, self.camera_orientation)

        # @TODO change image size
        pb.getCameraImage(128, 128, view_matrix, self.projection_matrix)

    def reset_positions(self):
        """Resets all recorded positions to 0."""
        for pos in self.positions:
            pos[0] = 0.0
            pos[1] = 0.0

    def set_position(self, position_index: int) -> None:
        """Sets the given position index with the current camera position.
        
        :param position_index: index of the position to set
        :raises ValueError: if the index is not between 0 and 5 included
        """
        if position_index < 0 or position_index > 5:
            raise ValueError('Invalid position index, must be between 0 and 5 included')

        joint_states = pb.getJointStates(self.main_link, self.joints)

        pan_joint_value = cast(float, joint_states[0][0])
        tilt_joint_value = cast(float, joint_states[1][0])

        self.positions[position_index] = [pan_joint_value, tilt_joint_value]

    def update(self, refresh_freq: float) -> None:
        """Updates camera zoom and renders an image.

        This method should not be called too often because
        some computations are slow.
        
        :param refresh_freq: frequency at which this method will be called
        """
        self.render_image()
        zoom_amount = ZOOM_SPEEDS[abs(self.zoom_speed)]
        zoom_direction = -1 if self.zoom_speed < 0 else 1

        new_fov = self.current_fov + zoom_direction * zoom_amount * refresh_freq

        if new_fov < self.ZOOM_FOV_MIN:
            new_fov = self.ZOOM_FOV_MIN

        if new_fov > self.ZOOM_FOV_MAX:
            new_fov = self.ZOOM_FOV_MAX

        if new_fov != self.current_fov:
            self.projection_matrix = compute_projection_matrix(new_fov)
            self.current_fov = new_fov


def compute_projection_matrix(fov):
    return pb.computeProjectionMatrixFOV(fov=fov, aspect=1.0, nearVal=0.1, farVal=100)
