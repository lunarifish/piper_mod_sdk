#!/usr/bin/env python3
"""
拖动示教例程：
- 按 r 开始录制 → 切换到 FreeMove 模式，录制关节轨迹
- 按 r 停止录制
- 按 p 回放录制的轨迹

用法:
    python teaching.py [--channel can0] [--rate 50]
"""

import argparse
import atexit
import sys
import termios
import threading
import time
import tty

from swerve_arm import ControlMode, SwerveArm


class KeyboardListener:
    """非阻塞键盘监听（后台线程 + raw 终端模式）。"""

    def __init__(self) -> None:
        self._last_key: str = ""
        self._lock = threading.Lock()
        self._running = True
        self._saved_attrs: list | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        fd = sys.stdin.fileno()
        self._saved_attrs = termios.tcgetattr(fd)
        tty.setraw(fd)
        atexit.register(self._restore)
        self._thread.start()

    def _restore(self) -> None:
        if self._saved_attrs is not None:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._saved_attrs)
            except termios.error:
                pass

    def stop(self) -> None:
        self._running = False
        self._restore()

    def _run(self) -> None:
        while self._running:
            try:
                ch = sys.stdin.read(1)
                if ch:
                    with self._lock:
                        self._last_key = ch.lower()
            except (OSError, EOFError):
                break

    def get_key(self) -> str:
        """消费并返回最后一次按键，无按键返回空字符串。"""
        with self._lock:
            key = self._last_key
            self._last_key = ""
        return key


class State:
    IDLE = "idle"
    RECORDING = "recording"
    PLAYBACK = "playback"


def main():
    parser = argparse.ArgumentParser(description="拖动示教例程")
    parser.add_argument("-c", "--channel", default="can0", help="CAN 接口名")
    parser.add_argument(
        "-r", "--rate", type=int, default=50,
        help="录制采样率 (Hz)，默认 50",
    )
    args = parser.parse_args()

    interval = 1.0 / args.rate

    arm = SwerveArm(channel=args.channel)
    kbd = KeyboardListener()

    try:
        # 等待上线
        print("[INFO] 等待机械臂上线 ...")
        while not arm.is_online():
            time.sleep(0.1)
        print("[INFO] 机械臂已上线")

        arm.enable_arm(True)
        time.sleep(0.5)
        arm.mode_ctrl(ControlMode.kNormal)
        time.sleep(0.3)

        kbd.start()

        state = State.IDLE
        trajectory: list[list[float]] = []

        print()
        print("=" * 50)
        print("  拖动示教控制")
        print("  r - 开始/停止录制")
        print("  p - 回放轨迹")
        print("  q - 退出")
        print("=" * 50)
        print()

        while True:
            key = kbd.get_key()

            if key == "q":
                print("[INFO] 退出")
                break

            # --- 录制切换 ---
            if key == "r":
                if state == State.IDLE:
                    state = State.RECORDING
                    trajectory.clear()
                    arm.mode_ctrl(ControlMode.kFreeMove)
                    print("[REC] 开始录制（拖动机械臂进行示教）...")
                elif state == State.RECORDING:
                    state = State.IDLE
                    arm.mode_ctrl(ControlMode.kNormal)
                    print(f"[REC] 停止录制，共 {len(trajectory)} 个采样点")

            # --- 回放 ---
            if key == "p":
                if state == State.RECORDING:
                    print("[WARN] 请先停止录制再回放")
                elif not trajectory:
                    print("[WARN] 没有录制的轨迹")
                elif state == State.IDLE:
                    state = State.PLAYBACK
                    arm.mode_ctrl(ControlMode.kNormal)
                    time.sleep(0.2)
                    print(f"[PLAY] 开始回放 ({len(trajectory)} 点, ~{len(trajectory)/args.rate:.1f}s)")
                    t0 = time.monotonic()
                    played = 0
                    for i, pos in enumerate(trajectory):
                        elapsed = time.monotonic() - t0
                        expected = i * interval
                        if expected > elapsed:
                            time.sleep(expected - elapsed)
                        arm.joint_ctrl(pos)
                        played += 1
                        if i % 20 == 0:
                            sys.stdout.write(f"\r[PLAY] {played}/{len(trajectory)}")
                            sys.stdout.flush()
                    print(f"\r[PLAY] 回放完成 ({played} 点)        ")
                    state = State.IDLE

            # --- 录制中采样 ---
            if state == State.RECORDING:
                js = arm.get_joint_state()
                if js is not None:
                    trajectory.append(list(js.position))
                    sys.stdout.write(f"\r[REC] {len(trajectory)} 个采样点  ")
                    sys.stdout.flush()

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n[INFO] 用户中断")
    finally:
        kbd.stop()
        arm.close()
        print("[INFO] 已关闭")


if __name__ == "__main__":
    main()
