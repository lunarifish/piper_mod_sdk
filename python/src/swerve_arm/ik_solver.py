
import math
from typing import Optional

import numpy as np


def _quat_to_rot(qx: float, qy: float, qz: float, qw: float) -> np.ndarray:
    """四元数 (xyzw) -> 旋转矩阵 (3×3)."""
    r = np.empty((3, 3), dtype=np.float64)
    r[0, 0] = 1.0 - 2.0 * (qy * qy + qz * qz)
    r[0, 1] = 2.0 * (qx * qy - qw * qz)
    r[0, 2] = 2.0 * (qx * qz + qw * qy)
    r[1, 0] = 2.0 * (qx * qy + qw * qz)
    r[1, 1] = 1.0 - 2.0 * (qx * qx + qz * qz)
    r[1, 2] = 2.0 * (qy * qz - qw * qx)
    r[2, 0] = 2.0 * (qx * qz - qw * qy)
    r[2, 1] = 2.0 * (qy * qz + qw * qx)
    r[2, 2] = 1.0 - 2.0 * (qx * qx + qy * qy)
    return r


def _optimize_angle(target_angle: float, current_angle: float) -> float:
    """角度平滑处理，防止角度频繁跳变
    """
    delta = target_angle - current_angle
    delta = (delta + math.pi) % (2.0 * math.pi)
    if delta < 0.0:
        delta += 2.0 * math.pi
    delta -= math.pi
    return current_angle + delta


class IKSolver:
    """6-DOF 解析逆运动学求解器.

    用法::

        solver = IKSolver()
        q = solver.solve(pose)           # 从零位起步
        q = solver.solve(pose, q_init)   # 从指定关节角起步
    """

    def __init__(
        self,
        tool_offset: float = 0.0,
    ) -> None:
        """构造求解器.

        Args:
            tool_offset: 工具在末端伸出的长度（单位m）.
        """
        # 机械臂几何参数 (单位m)
        self.l1: float = 0.33
        self.l2: float = 0.3595
        self.dz: float = 0.097
        self.tool_offset: float = float(tool_offset)

    def solve(
        self,
        pose: object,
        q_init: Optional[list[float]] = None,
    ) -> Optional[list[float]]:
        """求解逆运动学.

        Args:
            pose:   EndEffectorPose：目标末端位姿
            q_init: 当前关节角度 [j1..j6]

        Returns:
            6个关节角度[j1..j6]（弧度），或None表示目标不可达.
        """

        x = float(pose.x)
        y = float(pose.y)
        z = float(pose.z)
        R_target = _quat_to_rot(pose.qx, pose.qy, pose.qz, pose.qw)

        if self.tool_offset != 0.0:
            ax, ay, az = float(R_target[0, 2]), float(
                R_target[1, 2]), float(R_target[2, 2])
            x -= self.tool_offset * ax
            y -= self.tool_offset * ay
            z -= self.tool_offset * az

        if q_init is not None and len(q_init) >= 6:
            ref = [float(q_init[i]) for i in range(6)]
        else:
            ref = [0.0] * 6

        # 位置解
        a1 = math.atan2(y, x)

        r_val = math.hypot(x, y)
        z_eff = z - self.dz
        L_sq = r_val * r_val + z_eff * z_eff

        cos_t3 = (L_sq - self.l1 * self.l1 - self.l2 * self.l2) / (
            2.0 * self.l1 * self.l2
        )
        if abs(cos_t3) > 1.0:
            return None

        a3 = -math.acos(cos_t3)  # elbow up

        k1 = self.l1 + self.l2 * math.cos(a3)
        k2 = self.l2 * math.sin(a3)
        a2 = math.atan2(z_eff, r_val) - math.atan2(k2, k1)

        # 姿态解
        c1 = math.cos(a1)
        s1 = math.sin(a1)
        a23 = -(a2 + a3)
        ca = math.cos(a23)
        sa = math.sin(a23)

        # R03
        R03 = np.array(
            [
                [c1 * ca, -s1, c1 * sa],
                [s1 * ca, c1, s1 * sa],
                [-sa, 0.0, ca],
            ],
            dtype=np.float64,
        )

        W = R03.T @ R_target

        c5 = max(-1.0, min(1.0, float(W[0, 0])))
        a5 = math.acos(c5)

        if abs(math.sin(a5)) < 1e-7:
            # 奇异位形，a4任意取0
            a4 = 0.0
            a6 = math.atan2(float(W[2, 1]), float(W[1, 1]))
        else:
            a4 = math.atan2(float(W[1, 0]), -float(W[2, 0]))
            a6 = math.atan2(float(W[0, 1]), float(W[0, 2]))

        raw = [a1, a2, a3, a4, math.pi - a5, -a6]
        optimized = [_optimize_angle(raw[i], ref[i]) for i in range(6)]
        return optimized
