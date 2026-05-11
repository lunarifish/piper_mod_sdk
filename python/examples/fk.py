#!/usr/bin/env python3
"""
正运动学例程：读取关节位置，实时打印末端执行器笛卡尔坐标。

用法:
    python fk.py [--channel can0] [--rate 10]
"""

import argparse
import sys
import time

from swerve_arm import SwerveArm, ControlMode


def main():
    parser = argparse.ArgumentParser(description="末端位姿监控")
    parser.add_argument("-c", "--channel", default="can0", help="CAN 接口名")
    parser.add_argument(
        "-r", "--rate", type=int, default=10,
        help="刷新率 (Hz)，默认 10",
    )
    args = parser.parse_args()

    interval = 1.0 / args.rate
    arm = SwerveArm(channel=args.channel)

    try:
        print("[INFO] 等待机械臂上线 ...")
        while not arm.is_online():
            time.sleep(0.1)
        print("[INFO] 机械臂已上线\n")
        
        arm.enable_arm(True)
        arm.mode_ctrl(ControlMode.kFreeMove)
        

        header = (
            "     x (m)     y (m)     z (m)   "
            "|    qx       qy       qz       qw   "
            "| Joints (rad)"
        )
        divider = "-" * len(header)
        print(header)
        print(divider)

        while True:
            pose = arm.get_end_eff_pose()
            js = arm.get_joint_state()

            if js is not None:
                joint_str = " ".join(f"{q: 7.3f}" for q in js.position)
            else:
                joint_str = "---  ---  ---  ---  ---"

            line = (
                f"{pose.x: 9.4f} {pose.y: 9.4f} {pose.z: 9.4f} "
                f"| {pose.qx: 7.4f} {pose.qy: 7.4f} {pose.qz: 7.4f} {pose.qw: 7.4f} "
                f"| {joint_str}"
            )
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
