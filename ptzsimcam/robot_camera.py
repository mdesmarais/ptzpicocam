"""Defines a camera robot based on the EVI-D100 by Sony for pybullet."""
import math
from dataclasses import dataclass
from typing import Optional, Tuple, cast

import numpy as np
import pybullet as pb

from ptzsimcam.homogeneous_transform import rot_x, rot_z, translation

ZOOM_SPEEDS = [0, 1, 2, 5, 7, 10, 15, 20]
"""Association between a visca zoom speed (0, 7) and a zoom speed in degrees/s."""


@dataclass
class ParamsMemory:

    """Parameters of the camera that have been saved."""

    pan_joint_value: float
    tilt_joint_value: float
    zoom_fov: float

    @property
    def joints(self) -> Tuple[float, float]:
        """Gets joint values (pan and tilt) as a tuple of float"""
        return (self.pan_joint_value, self.tilt_joint_value)


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

        # Recorded params, 6 available
        self.memories = [ParamsMemory(0.0, 0.0, self.ZOOM_FOV_MAX) for _ in range(6)]
        self.target_memory: Optional['ParamsMemory'] = None

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

    @property
    def is_busy(self) -> bool:
        """Returns True if the camera is executing a command, otherwise False."""
        return not self.target_memory is None

    def read_joints(self) -> Tuple[float, float]:
        """Reads joint values (pan, tilt) and returns them as a tuple
        
        :returns: a tuple containing joint values.
        """
        joint_states = pb.getJointStates(self.main_link, self.joints)

        pan_joint_value = cast(float, joint_states[0][0])
        tilt_joint_value = cast(float, joint_states[1][0])

        return (pan_joint_value, tilt_joint_value)

    def recall_memory(self, memory_index: int) -> None:
        """Updates camera with parameters recorded at the given index.
        
        :param memory_index: index of the memory to recall
        :raises ValueError: if the index is not between 0 and 5 included
        """
        if memory_index < 0 or memory_index > 5:
            raise ValueError('Invalid memory index, must be between 0 and 5 included')

        self.target_memory = self.memories[memory_index]
        target_fov = self.target_memory.zoom_fov

        new_fov_distance = self.current_fov - target_fov

        if new_fov_distance > 0:
            self.zoom_speed = -4
        elif new_fov_distance < 0:
            self.zoom_speed = 4
        else:
            self.zoom_speed = 0

        pb.setJointMotorControlArray(
            self.main_link, self.joints, 
            pb.POSITION_CONTROL, targetPositions=self.target_memory.joints,
            forces=[0.3, 0.3], positionGains=[0.01, 0.01]
        )

    def render_image(self):
        """Renders an image using the simulated camera of pybullet.
        
        The camera will be placed at the end of the robot.
        """
        world_from_tool = self.get_base_from_camera()
        tool_pos = world_from_tool[:3, 3]

        direction = world_from_tool[:3, :3].dot(self.camera_direction)
        view_matrix = pb.computeViewMatrix(tool_pos, direction, self.camera_orientation)

        pb.getCameraImage(128, 128, view_matrix, self.projection_matrix, flags=pb.ER_NO_SEGMENTATION_MASK)

    def set_memory(self, memory_index: int) -> None:
        """Sets the given memory index with the current camera parameters.
        
        :param memory_index: index of the memory to set
        :raises ValueError: if the index is not between 0 and 5 included
        """
        if memory_index < 0 or memory_index > 5:
            raise ValueError('Invalid memory index, must be between 0 and 5 included')

        pan_joint_value, tilt_joint_value = self.read_joints()

        self.memories[memory_index] = ParamsMemory(pan_joint_value, tilt_joint_value, self.current_fov)

    def update(self, refresh_freq: float) -> None:
        """Updates camera zoom and renders an image.

        This method should not be called too often because
        some computations are slow.
        
        :param refresh_freq: frequency at which this method will be called
        """
        self.render_image()

        if not self.target_memory is None:
            joints = self.read_joints()

            if np.allclose(self.target_memory.joints, joints, atol=1e-1) and self.current_fov == self.target_memory.zoom_fov:
                self.target_memory = None

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
