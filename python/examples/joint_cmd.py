#!/usr/bin/env python3
"""
最小例程：使能机械臂并移动到指定关节角度。

用法:
    python joint_cmd.py [--channel can0]
"""

import argparse
import time

from swerve_arm import ControlMode, SwerveArm

TARGET = [0.0, 1.57, -1.57, 0.0, 0.0]


def main():
    parser = argparse.ArgumentParser(description="关节控制例程")
    parser.add_argument("-c", "--channel", default="can0", help="CAN 接口名")
    args = parser.parse_args()

    arm = SwerveArm(channel=args.channel)
    try:
        # 等待机械臂上线
        print("等待机械臂上线 ...")
        while not arm.is_online():
            time.sleep(0.1)
        print("机械臂已上线")

        print("使能机械臂 ...")
        arm.enable_arm(True)
        time.sleep(0.5)

        print("切换到正常位控模式 ...")
        arm.mode_ctrl(ControlMode.kNormal)
        time.sleep(0.3)

        print(f"下发目标角度: {TARGET}")
        arm.joint_ctrl(TARGET)

        print("等待机械臂到位 ...")
        time.sleep(3.0)

        # 读取当前关节状态
        js = arm.get_joint_state()
        if js is not None:
            print(f"当前关节角度: {[f'{q:.3f}' for q in js.position]}")
        else:
            print("WANRING 未收到关节反馈")
            
        print("失能机械臂 ...")
        arm.enable_arm(False)
        time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        arm.close()
        print("已关闭")


if __name__ == "__main__":
    main()
