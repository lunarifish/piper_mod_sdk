"""
SwerveArm main class entry
"""

import struct
import threading
from collections.abc import Callable
from importlib import resources
from typing import Optional

import can

from .rx_daemon import JointState, PressureSensorData, RxDaemon, SystemStatus


class ControlMode:
    """Host → Arm命令，ModeCtrlCommand."""
    kFreeMove: int = 0  # 机械臂不使力，外力可拖动（用于拖动示教）
    kNormal: int = 1    # 正常关节位控模式


# 帧 ID 偏移量
_OFFSET_ENABLE = 4
_OFFSET_MODE_CTRL = 5
_OFFSET_JOINT_CTRL = 6


class EndEffectorPose:
    """末端执行器笛卡尔位姿.

        x, y, z:  位置 (m).
        qx, qy, qz, qw: 四元数姿态 (xyzw).
    """

    __slots__ = ("x", "y", "z", "qx", "qy", "qz", "qw")

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        qx: float = 0.0,
        qy: float = 0.0,
        qz: float = 0.0,
        qw: float = 1.0,
    ):
        self.x = x
        self.y = y
        self.z = z
        self.qx = qx
        self.qy = qy
        self.qz = qz
        self.qw = qw

    @classmethod
    def from_list(cls, values: list[float]) -> "EndEffectorPose":
        """从 [x, y, z, qx, qy, qz, qw] 构造."""
        return cls(*values)

    def to_list(self) -> list[float]:
        """转为 [x, y, z, qx, qy, qz, qw]."""
        return [self.x, self.y, self.z, self.qx, self.qy, self.qz, self.qw]

    def __repr__(self) -> str:
        return (
            f"EndEffectorPose(x={self.x:.4f}, y={self.y:.4f}, z={self.z:.4f}, "
            f"qx={self.qx:.4f}, qy={self.qy:.4f}, qz={self.qz:.4f}, qw={self.qw:.4f})"
        )


class SwerveArm:
    """机械臂控制类。

    通过 SocketCAN 与下位机通信，提供机械臂控制与状态读取接口。
    示例用法::
        arm = SwerveArm(channel="can0")
        arm.enable_arm(True)
        arm.mode_ctrl(ControlMode.kNormal)

        # 关节控制
        arm.joint_ctrl([0.0, -0.5, 0.0, 1.0, 0.0])
        js = arm.get_joint_state()

        # 末端笛卡尔控制
        pose = arm.get_end_eff_pose()
        target = EndEffectorPose(0.3, 0.0, 0.2, 0, 0, 0, 1)
        arm.end_pose_ctrl(target)

        arm.close()
    """

    _URDF_RESOURCE = "resources/swerve.urdf"

    def __init__(
        self,
        channel: str = "can0",
        base_frame_id: int = 0x233,
        watchdog_timeout: float = 1.0,
    ):
        """
        Args:
            channel:          SocketCAN 接口名.
            base_frame_id:    基础帧 ID.
            watchdog_timeout: 看门狗超时时间 (秒).
        """
        self._channel = channel
        self._base_frame_id = base_frame_id

        # CAN发送总线
        self._send_bus = can.interface.Bus(
            bustype="socketcan", channel=channel, fd=True
        )
        self._send_lock = threading.Lock()

        # 接收守护线程
        self._rx = RxDaemon(
            channel=channel,
            base_frame_id=base_frame_id,
            watchdog_timeout=watchdog_timeout,
        )

        # 加载URDF模型
        self._pin_model: object
        self._pin_data: object
        self._end_eff_frame_id: int = -1
        self._load_pinocchio_model()

    def _load_pinocchio_model(self) -> None:
        """从内置资源加载 URDF 模型到 Pinocchio."""
        try:
            import pinocchio as pin  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "pinocchio 未安装，无法使用末端控制功能。"
                "请执行: pip install pin"
            )

        ref = resources.files("swerve_arm") / self._URDF_RESOURCE
        with resources.as_file(ref) as urdf_path:
            self._pin_model = pin.buildModelFromUrdf(str(urdf_path))

        self._pin_data = self._pin_model.createData()

        if self._pin_model.existFrame("END_EFF"):
            self._end_eff_frame_id = self._pin_model.getFrameId("END_EFF")
        else:
            self._end_eff_frame_id = self._pin_model.njoints - 1

    def _send_frame(self, offset: int, payload: bytes) -> None:
        """发送一帧 CAN FD 数据."""
        frame_id = self._base_frame_id + offset
        msg = can.Message(
            arbitration_id=frame_id,
            data=payload,
            is_fd=True,
            is_extended_id=False,
        )
        with self._send_lock:
            try:
                self._send_bus.send(msg)
            except can.CanError as e:
                raise RuntimeError(
                    f"CAN 发送失败 (frame_id=0x{frame_id:X}): {e}") from e

    def enable_arm(self, enable: bool) -> None:
        """使能/失能机械臂。

        Args:
            enable: True 使能，False 失能.
        """
        payload = struct.pack("<B", 1 if enable else 0)
        self._send_frame(_OFFSET_ENABLE, payload)

    def mode_ctrl(self, mode: int) -> None:
        """切换控制模式。

        Args:
            mode: ControlMode.kFreeMove (可自由移动) 或 ControlMode.kNormal (正常位控).
        """
        payload = struct.pack("<B", mode)
        self._send_frame(_OFFSET_MODE_CTRL, payload)

    def joint_ctrl(self, positions: list[float]) -> None:
        """下发 5 轴关节目标角度，驱动机械臂运动。

        Args:
            positions: 5 个关节目标角度 [j1..j5]，单位 rad.
        """
        if len(positions) != 5:
            raise ValueError(f"需要 5 个关节角度，收到 {len(positions)} 个")
        payload = struct.pack("<5f", *positions)
        self._send_frame(_OFFSET_JOINT_CTRL, payload)

    # ------------------------------------------------------------------
    # 状态读取
    def get_joint_state(self) -> Optional[JointState]:
        """读取最新关节状态（角度/速度/力矩）."""
        return self._rx.get_joint_state()

    def get_system_status(self) -> Optional[SystemStatus]:
        """读取最新系统状态."""
        return self._rx.get_system_status()

    def get_pressure(self) -> Optional[PressureSensorData]:
        """读取最新压力传感器数据."""
        return self._rx.get_pressure()

    # ------------------------------------------------------------------
    # 在线监测
    def is_online(self) -> bool:
        """返回机械臂是否在线."""
        return self._rx.is_online()

    def register_online_callback(self, cb: Callable[[bool], None]) -> None:
        """注册在线状态变更回调."""
        self._rx.register_online_callback(cb)

    def unregister_online_callback(self, cb: Callable[[bool], None]) -> None:
        """取消在线状态变更回调."""
        self._rx.unregister_online_callback(cb)

    def get_end_eff_pose(self) -> EndEffectorPose:
        """读取末端执行器当前位姿（通过正运动学估算）。

        Returns:
            EndEffectorPose: 末端位姿 (x, y, z, qx, qy, qz, qw).
        """
        import pinocchio as pin  # type: ignore[import-untyped]

        js = self._rx.get_joint_state()
        if js is None:
            raise RuntimeError("无关节数据，无法计算末端位姿")

        q = pin.neutral(self._pin_model)
        q[:5] = js.position

        pin.forwardKinematics(self._pin_model, self._pin_data, q)
        pin.updateFramePlacements(self._pin_model, self._pin_data)

        placement = self._pin_data.oMf[self._end_eff_frame_id]
        pos = placement.translation
        quat = pin.Quaternion(placement.rotation)

        return EndEffectorPose(
            x=float(pos[0]),
            y=float(pos[1]),
            z=float(pos[2]),
            qx=float(quat.x),
            qy=float(quat.y),
            qz=float(quat.z),
            qw=float(quat.w),
        )

    def end_pose_ctrl(
        self,
        target: EndEffectorPose,
        max_iter: int = 200,
        tol: float = 1e-4,
        dt: float = 0.1,
        damping: float = 1e-3,
    ) -> None:
        """末端笛卡尔位姿控制（逆运动学 + 关节控制）。

        使用Pinocchio雅可比矩阵进行阻尼最小二乘迭代IK，
        然后将关节角度下发给机械臂。

        Args:
            target:   目标末端位姿.
            max_iter: IK最大迭代次数.
            tol:      收敛阈值 (位姿误差范数).
            dt:       每次迭代步长系数.
            damping:  阻尼最小二乘阻尼因子.
        """
        import numpy as np  # type: ignore[import-untyped]
        import pinocchio as pin  # type: ignore[import-untyped]

        # 获取当前关节角度作为 IK 初始值
        js = self._rx.get_joint_state()
        if js is None:
            raise RuntimeError("无关节数据，无法执行末端控制")

        q = np.array(js.position, dtype=np.float64)

        # 目标位姿 SE3
        target_se3 = pin.SE3(
            pin.Quaternion(target.qx, target.qy, target.qz, target.qw),
            np.array([target.x, target.y, target.z]),
        )

        identity6 = np.eye(6)

        for _ in range(max_iter):
            pin.forwardKinematics(self._pin_model, self._pin_data, q)
            pin.updateFramePlacements(self._pin_model, self._pin_data)

            # 位姿误差 (se3切空间)
            current_placement = self._pin_data.oMf[self._end_eff_frame_id]
            error = pin.log(current_placement.inverse() * target_se3)
            if np.linalg.norm(error.vector) < tol:
                break

            # 末端frame雅可比 (世界坐标系)
            J = pin.computeFrameJacobian(
                self._pin_model,
                self._pin_data,
                q,
                self._end_eff_frame_id,
                pin.ReferenceFrame.WORLD,
            )

            # 阻尼最小二乘
            JJt = J @ J.T
            J_pinv = J.T @ np.linalg.solve(JJt +
                                           damping * identity6, identity6)
            dq = J_pinv @ error.vector
            q += dq * dt

        self.joint_ctrl(q[:5].tolist())

    def close(self) -> None:
        """失能机械臂，关闭 CAN 通信，并停止守护线程."""
        self.enable_arm(False)
        self._rx.close()
        self._send_bus.shutdown()
