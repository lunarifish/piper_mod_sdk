import { useState, useCallback, useRef } from 'react';

/** 串口连接状态 */
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';

/** 一条字节流记录 */
export interface ByteLogEntry {
  /** 毫秒时间戳 */
  ts: number;
  /** 原始字节 */
  data: Uint8Array;
}

/** 串口固定参数 */
const SERIAL_OPTIONS: SerialOptions = {
  baudRate: 921600,
  dataBits: 8,
  stopBits: 1,
  parity: 'none',
  flowControl: 'none',
};

function makePortLabel(port: SerialPort): string {
  try {
    const info = port.getInfo();
    const vid = info.usbVendorId?.toString(16).padStart(4, '0') ?? '????';
    const pid = info.usbProductId?.toString(16).padStart(4, '0') ?? '????';
    return `USB VID:0x${vid} PID:0x${pid}`;
  } catch {
    return 'Unknown Serial Port';
  }
}

/**
 * Web Serial API 串口通信 hook
 *
 * 使用浏览器原生 Web Serial API (Chromium 内核浏览器支持)。
 * 通信协议尚未敲定，sendAllParams/readAllParams 仅构建占位帧。
 * 内置 TX/RX 字节流日志，用于 SerialTerminal 展示。
 */
export function useSerial() {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [ports, setPorts] = useState<string[]>([]);
  const [selectedPort, setSelectedPort] = useState<string>('');
  const portRef = useRef<SerialPort | null>(null);
  const writerRef = useRef<WritableStreamDefaultWriter<Uint8Array> | null>(null);
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);
  const readLoopAbortRef = useRef<AbortController | null>(null);

  // ---- TX/RX 日志 ----
  const [txLog, setTxLog] = useState<ByteLogEntry[]>([]);
  const [rxLog, setRxLog] = useState<ByteLogEntry[]>([]);
  const [txBytes, setTxBytes] = useState(0);
  const [rxBytes, setRxBytes] = useState(0);

  /** 写入帧并记录到 TX 日志 */
  const writeFrame = useCallback(async (data: Uint8Array) => {
    if (!writerRef.current) {
      console.error('串口未连接');
      return;
    }
    await writerRef.current.write(data);
    setTxLog((prev) => [...prev.slice(-255), { ts: Date.now(), data }]);
    setTxBytes((n) => n + data.length);
  }, []);

  /** 背景读取循环 */
  const startReadLoop = useCallback((port: SerialPort) => {
    const abort = new AbortController();
    readLoopAbortRef.current = abort;

    (async () => {
      while (port.readable && !abort.signal.aborted) {
        try {
          const reader = port.readable.getReader();
          readerRef.current = reader;
          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            if (value && value.length > 0) {
              setRxLog((prev) => [...prev.slice(-255), { ts: Date.now(), data: value }]);
              setRxBytes((n) => n + value.length);
            }
          }
          reader.releaseLock();
        } catch {
          // 端口断开或读取错误，退出循环
          break;
        }
      }
    })();
  }, []);

  /** 扫描可用串口 —— 弹出浏览器串口选择器，同时列出已授权端口 */
  const scanPorts = useCallback(async () => {
    try {
      const authorized = await navigator.serial.getPorts();
      const labels = authorized.map(makePortLabel);
      setPorts(labels);
      if (labels.length > 0 && !selectedPort) {
        setSelectedPort(labels[0]);
      }

      try {
        const newPort = await navigator.serial.requestPort();
        const newLabel = makePortLabel(newPort);
        if (!labels.includes(newLabel)) {
          setPorts([...labels, newLabel]);
        }
        setSelectedPort(newLabel);
        portRef.current = newPort;
      } catch {
        // 用户取消选择
      }
    } catch (e) {
      console.error('扫描串口失败:', e);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** 连接串口，返回 true 表示成功 */
  const connect = useCallback(async (): Promise<boolean> => {
    if (!portRef.current) {
      console.error('没有可用的串口，请先扫描');
      return false;
    }
    setStatus('connecting');
    try {
      const port = portRef.current;
      await port.open(SERIAL_OPTIONS);

      const writer = port.writable!.getWriter();
      writerRef.current = writer;

      // 启动背景读取循环
      startReadLoop(port);

      port.addEventListener('disconnect', () => {
        readLoopAbortRef.current?.abort();
        readLoopAbortRef.current = null;
        setStatus('disconnected');
        portRef.current = null;
        writerRef.current = null;
        readerRef.current = null;
      });

      setStatus('connected');
      console.log('串口已连接 (921600 8N1)');
      return true;
    } catch (e) {
      console.error('连接失败:', e);
      setStatus('disconnected');
      return false;
    }
  }, [startReadLoop]);

  /** 断开串口 */
  const disconnect = useCallback(async () => {
    try {
      readLoopAbortRef.current?.abort();
      readLoopAbortRef.current = null;
      if (readerRef.current) {
        try { readerRef.current.releaseLock(); } catch {}
        readerRef.current = null;
      }
      if (writerRef.current) {
        await writerRef.current.close();
        writerRef.current = null;
      }
      if (portRef.current) {
        await portRef.current.close();
        portRef.current = null;
      }
    } catch (e) {
      console.error('断开失败:', e);
    }
    setStatus('disconnected');
    setTxLog([]);
    setRxLog([]);
    setTxBytes(0);
    setRxBytes(0);
  }, []);

  // ---- 通信协议占位 ----
  // TODO: 待下位机协议敲定后实现具体帧格式

  /** 批量发送全部关节参数，返回 true 表示已发送 */
  const sendAllParams = useCallback(
    async (allValues: Map<string, Map<string, number>>): Promise<boolean> => {
      const payload: { joint: string; key: string; value: number }[] = [];
      for (const [joint, params] of allValues) {
        for (const [key, value] of params) {
          payload.push({ joint, key, value });
        }
      }

      // TODO: 协议敲定后填充真实帧
      const frame = new Uint8Array(0);
      if (frame.length === 0) {
        console.warn('协议帧为空，跳过发送（协议未实现）');
        console.log('[占位] 发送全部参数:', payload);
        return false;
      }

      try {
        await writeFrame(frame);
        console.log('[占位] 发送全部参数:', payload);
        return true;
      } catch (e) {
        console.error('发送参数失败:', e);
        return false;
      }
    },
    [writeFrame],
  );

  /** 向 MCU 发送读指令，接收 QSPI Flash 中的所有参数 */
  const readAllParams = useCallback(async (): Promise<Map<string, Map<string, number>> | null> => {
    console.log('[占位] 发送读指令，等待 MCU 返回参数...');

    // TODO: 协议敲定后填充真实读指令帧、解析响应
    const frame = new Uint8Array(0);
    if (frame.length === 0) {
      console.warn('协议帧为空，跳过读取（协议未实现）');
      return null;
    }

    try {
      await writeFrame(frame);
      // TODO: 从 rxLog 或专用 reader 解析响应
    } catch (e) {
      console.error('读取参数失败:', e);
      return null;
    }

    return null;
  }, [writeFrame]);

  return {
    status,
    ports,
    selectedPort,
    setSelectedPort,
    scanPorts,
    connect,
    disconnect,
    sendAllParams,
    readAllParams,
    /** TX 字节流日志 */
    txLog,
    /** RX 字节流日志 */
    rxLog,
    /** 累计发送字节数 */
    txBytes,
    /** 累计接收字节数 */
    rxBytes,
  };
}
