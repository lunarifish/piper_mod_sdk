#!/usr/bin/env python3
"""
IK 验证例程：实时对比 FK、IK 往返精度。

用法:
    python ik.py [--channel can0] [--rate 5]
"""

import argparse
import sys
import time

from swerve_arm import ControlMode, SwerveArm


def main():
    parser = argparse.ArgumentParser(description="IK 往返精度验证")
    parser.add_argument("-c", "--channel", default="can0", help="CAN 接口名")
    parser.add_argument(
        "-r", "--rate", type=int, default=5,
        help="刷新率 (Hz)，默认 5",
    )
    args = parser.parse_args()

    interval = 1.0 / args.rate
    arm = SwerveArm(channel=args.channel)

    try:
        print("[INFO] 等待机械臂上线 ...")
        while not arm.is_online():
            time.sleep(0.1)
        print("[INFO] 机械臂已上线")

        arm.enable_arm(True)
        time.sleep(0.5)
        arm.mode_ctrl(ControlMode.kFreeMove)
        print("[INFO] 切换到自由运动模式，拖动机械臂进行测试\n")

        header = (
            "   原始关节 (FK→IK 输入)          "
            "| FK 末端位置 (m)              "
            "| IK 关节 (输出)                 "
            "| 误差 (°)"
        )
        divider = "-" * len(header)
        print(header)
        print(divider)

        while True:
            js = arm.get_joint_state()
            if js is None:
                sys.stdout.write("\r[WAIT] 等待关节数据...")
                sys.stdout.flush()
                time.sleep(interval)
                continue

            # ── 原始关节 ──
            q_in = list(js.position)

            # ── FK ──
            pose = arm.get_end_eff_pose()

            # ── IK ──
            q_ik = arm._ik_solver.solve(pose)

            # ── 误差 ──
            if q_ik is not None:
                err_deg = [
                    (float(q_ik[i]) - q_in[i]) * 57.2958 for i in range(5)
                ]
                err_str = " ".join(f"{e: 7.2f}" for e in err_deg)
                q_ik_str = " ".join(f"{q: 7.3f}" for q in q_ik)
            else:
                q_ik_str = "---  ---  ---  ---  ---"
                err_str = "---  ---  ---  ---  ---"

            q_in_str = " ".join(f"{q: 7.3f}" for q in q_in)
            pose_str = (
                f"({pose.x: 7.4f} {pose.y: 7.4f} {pose.z: 7.4f})"
            )

            line = f"{q_in_str} | {pose_str} | {q_ik_str} | {err_str}"
            sys.stdout.write(f"\r{line}")
            sys.stdout.flush()

            if not arm.is_online():
                print("\n[WARN] 机械臂离线")
                while not arm.is_online():
                    time.sleep(0.2)
                print("[INFO] 机械臂恢复在线")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n[INFO] 用户中断")
    finally:
        arm.close()
        print("[INFO] 已关闭")


if __name__ == "__main__":
    main()
