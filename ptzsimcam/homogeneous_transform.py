"""Defines functions for applying transformations on matrices."""
import math

import numpy as np


def rot_x(alpha):
    """Return the 4x4 homogeneous transform corresponding to a rotation of
    alpha around x
    """
    c = math.cos(alpha)
    s = math.sin(alpha)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]])


def rot_y(alpha):
    """Return the 4x4 homogeneous transform corresponding to a rotation of
    alpha around y
    """
    c = math.cos(alpha)
    s = math.sin(alpha)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]])


def rot_z(alpha):
    """Return the 4x4 homogeneous transform corresponding to a rotation of
    alpha around z
    """
    c = math.cos(alpha)
    s = math.sin(alpha)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])


def translation(vec):
    """Return the 4x4 homogeneous transform corresponding to a translation of
    vec
    """
    T = np.zeros(shape=(4, 4))
    T[:3, :3] = np.identity(3)
    T[:3, 3] = vec
    T[3, 3] = 1
    return T

