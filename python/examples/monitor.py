#!/usr/bin/env python3
"""
监控例程：循环打印关节位置、机械臂状态 (FSM) 和压力。

用法:
    python monitor.py [--channel can0] [--rate 10]
"""

import argparse
import sys
import time

from swerve_arm import FsmState, SwerveArm

FSM_NAMES: dict[int, str] = {
    FsmState.kInit:        "INIT",
    FsmState.kNoForce:     "NO_FORCE",
    FsmState.kManual:      "MANUAL",
    FsmState.kIdle:        "IDLE",
    FsmState.kHostControl: "HOST_CTRL",
    FsmState.kSequencing:  "SEQUENCING",
    FsmState.kFault:       "FAULT",
}


def fsm_name(state: int) -> str:
    return FSM_NAMES.get(state, f"UNKNOWN({state})")


def motor_status_label(code: int) -> str:
    """简单的电机状态标签，可根据下位机协议扩展."""
    return "OK" if code == 0 else f"ERR({code})"


def main():
    parser = argparse.ArgumentParser(description="机械臂状态监控")
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

        header = (
            "  q1      q2      q3      q4      q5    "
            "| FSM        | VBUS  | MOTORS               | PRESSURE"
        )
        divider = "-" * len(header)

        print(header)
        print(divider)

        while True:
            js = arm.get_joint_state()
            st = arm.get_system_status()
            pr = arm.get_pressure()

            # 关节角度
            if js is not None:
                pos_str = " ".join(f"{q: 7.3f}" for q in js.position)
            else:
                pos_str = "  ---     ---     ---     ---     ---  "

            # FSM + 电压
            if st is not None:
                fsm_str = f"{fsm_name(st.fsm_state):<10}"
                vbus_str = f"{st.vbus: 6.2f}V"
                motors = " ".join(
                    motor_status_label(s)
                    for s in (st.j1_motor_status, st.j2_motor_status,
                              st.j3_motor_status, st.j4_motor_status,
                              st.j5_motor_status)
                )
            else:
                fsm_str = "---       "
                vbus_str = "  ---  "
                motors = "--- --- --- --- ---"

            # 压力
            press_str = f"{pr.pressure: 8.2f} N" if pr is not None else "     ---  "

            line = f"{pos_str}| {fsm_str}| {vbus_str}| {motors:<21} | {press_str}"
            sys.stdout.write(f"\r{line}")
            sys.stdout.flush()

            # 在线状态变化时换行提示
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
