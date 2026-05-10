#!/usr/bin/env python3
"""
数据采集脚本：从 SocketCAN 接收关节状态帧（CAN ID=0x233），按 Enter 键采集一组数据，保存为 CSV 文件。
用于重力参数 b1, b2 的辨识回归。

下位机发送格式（CAN FD 帧，标准帧 ID=0x233）：
  ETL_PACKED_STRUCT(JointState) {
    float position[5];  // rad
    float velocity[5];  // rad/s
    float effort[5];    // N*m
  };
  // sizeof(JointState) == 60B

使用方法:
  python3 capture_data_can.py [--channel can0] [--output data.csv]

操作流程:
  1. 将机械臂置于某个静止姿态
  2. 按 Enter 采集当前关节角度和力矩
  3. 重复以上步骤，采集足够多的数据点(~20-50个)，覆盖不同的姿态
  4. 按 q + Enter 退出并保存
"""

import argparse
import csv
import os
import struct
import sys
import threading
from datetime import datetime

import can


FIELDNAMES = [
    "stamp",
    "q1", "q2", "q3", "q4", "q5",
    "dq1", "dq2", "dq3", "dq4", "dq5",
    "tau1", "tau2", "tau3", "tau4", "tau5",
]

CAN_ID = 0x233
PAYLOAD_SIZE = 60  # 15 × 4 bytes
NUM_JOINTS = 5


class CanReader:
    """后台线程持续读取 CAN 总线，保留最新一帧有效数据。"""

    def __init__(self, channel: str):
        self._channel = channel
        self._latest: dict | None = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        self._bus = can.interface.Bus(
            bustype="socketcan", channel=channel, fd=True
        )
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        print(f"[INFO] 已连接 CAN 接口 {channel}，监听 ID=0x{CAN_ID:03X}")

    def _read_loop(self):
        while not self._stop_event.is_set():
            try:
                msg = self._bus.recv(timeout=0.5)
                if msg is None:
                    continue
                if msg.arbitration_id != CAN_ID:
                    continue
                data = msg.data
                if len(data) < PAYLOAD_SIZE:
                    continue

                # 小端序，15 个 float32
                values = struct.unpack("<15f", data[:PAYLOAD_SIZE])
                positions = values[0:5]
                velocities = values[5:10]
                efforts = values[10:15]

                sample = {
                    "stamp": msg.timestamp,
                    "q1": positions[0], "q2": positions[1], "q3": positions[2],
                    "q4": positions[3], "q5": positions[4],
                    "dq1": velocities[0], "dq2": velocities[1], "dq3": velocities[2],
                    "dq4": velocities[3], "dq5": velocities[4],
                    "tau1": efforts[0], "tau2": efforts[1], "tau3": efforts[2],
                    "tau4": efforts[3], "tau5": efforts[4],
                }
                with self._lock:
                    self._latest = sample
            except (can.CanError, OSError, struct.error):
                continue

    def get_latest(self) -> dict | None:
        with self._lock:
            return dict(self._latest) if self._latest else None

    def close(self):
        self._stop_event.set()
        self._bus.shutdown()


def main():
    parser = argparse.ArgumentParser(description="从 SocketCAN 手动采集关节数据")
    parser.add_argument(
        "-c", "--channel", default="can0", help="CAN 接口名（默认 can0）"
    )
    default_output = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    )
    parser.add_argument(
        "-o", "--output", default=default_output, help="输出 CSV 文件路径"
    )
    args = parser.parse_args()

    try:
        reader = CanReader(args.channel)
    except (can.CanError, OSError) as e:
        print(f"[ERROR] 无法打开 CAN 接口 {args.channel}: {e}", file=sys.stderr)
        sys.exit(1)

    samples: list[dict] = []

    print("按 Enter 采集一组数据，输入 q 退出并保存。")

    try:
        while True:
            try:
                line = input()
            except EOFError:
                break

            if line.strip().lower() == "q":
                break

            sample = reader.get_latest()
            if sample is None:
                print("[WARN] 尚未收到有效数据，请确认 CAN 接口连接和下位机是否正常发送。")
                continue

            samples.append(sample)
            n = len(samples)
            print(
                f"[#{n}] q=({sample['q1']:.4f}, {sample['q2']:.4f}, {sample['q3']:.4f}, "
                f"{sample['q4']:.4f}, {sample['q5']:.4f})  "
                f"tau=({sample['tau1']:.4f}, {sample['tau2']:.4f}, {sample['tau3']:.4f}, "
                f"{sample['tau4']:.4f}, {sample['tau5']:.4f})"
            )
    except KeyboardInterrupt:
        pass
    finally:
        reader.close()

    if not samples:
        print("[WARN] 没有采集到数据，不保存文件。")
        return

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(samples)

    print(f"[INFO] 已保存 {len(samples)} 组数据到 {args.output}")


if __name__ == "__main__":
    main()
