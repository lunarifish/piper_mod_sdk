import { useState, useCallback, useEffect } from "react";
import {
  Box,
  Flex,
  SimpleGrid,
  Button,
  HStack,
} from "@chakra-ui/react";
import { AppToaster, toaster } from "./components/ui/toaster";
import { JOINT_SCHEMAS, buildDefaultValues } from "./schemas/params";
import { ConnectionBar } from "./components/ConnectionBar";
import { JointCard } from "./components/JointCard";
import { SerialTerminal } from "./components/SerialTerminal";
import { useSerial } from "./hooks/useSerial";

function App() {
  const serial = useSerial();

  const [allValues, setAllValues] = useState(() =>
    buildDefaultValues(JOINT_SCHEMAS),
  );

  useEffect(() => {
    serial.scanPorts();
  }, []);

  const isConnected = serial.status === "connected";

  const handleParamChange = useCallback(
    (jointName: string, key: string, value: number) => {
      setAllValues((prev) => {
        const next = new Map(prev);
        const jointValues = new Map(next.get(jointName));
        jointValues.set(key, value);
        next.set(jointName, jointValues);
        return next;
      });
    },
    [],
  );

  /** 连接串口 */
  const handleConnect = useCallback(async () => {
    const ok = await serial.connect();
    if (ok) {
      toaster.create({
        title: "串口已连接",
        description: "921600 8N1",
        type: "success",
      });
    } else {
      toaster.create({
        title: "连接失败",
        description: "无法打开串口，请检查设备",
        type: "error",
      });
    }
  }, [serial]);

  /** 断开串口 */
  const handleDisconnect = useCallback(async () => {
    await serial.disconnect();
    toaster.create({ title: "串口已断开", type: "info" });
  }, [serial]);

  /** 一键发送全部关节的所有参数 */
  const handleSendAll = useCallback(async () => {
    const ok = await serial.sendAllParams(allValues);
    if (ok) {
      toaster.create({
        title: "发送成功",
        description: "所有参数已写入串口",
        type: "success",
      });
    } else {
      toaster.create({
        title: "发送失败",
        description: "协议未实现，参数未发送",
        type: "warning",
      });
    }
  }, [allValues, serial]);

  /** 从 MCU 读取所有参数并更新 UI */
  const handleReadAll = useCallback(async () => {
    const result = await serial.readAllParams();
    if (result) {
      setAllValues(result);
      toaster.create({
        title: "读取成功",
        description: "MCU 参数已同步到界面",
        type: "success",
      });
    } else {
      toaster.create({
        title: "读取失败",
        description: "协议未实现或串口无响应",
        type: "warning",
      });
    }
  }, [serial]);

  return (
    <Box
      minH="100vh"
      h="100vh"
      display="flex"
      flexDirection="column"
      bg="gray.50"
    >
      <AppToaster />
      <Flex
        as="header"
        px={6}
        py={3}
        bg="white"
        borderBottomWidth="1px"
        borderColor="gray.200"
        align="center"
        justify="space-between"
        flexShrink={0}
        gap={4}
        flexWrap="wrap"
        boxShadow="sm"
      >
        <ConnectionBar
          status={serial.status}
          ports={serial.ports}
          selectedPort={serial.selectedPort}
          onSelectPort={serial.setSelectedPort}
          onScan={serial.scanPorts}
          onConnect={handleConnect}
          onDisconnect={handleDisconnect}
        />

        <HStack gap={2} flexShrink={0}>
          <Button
            size="sm"
            colorPalette="green"
            variant="solid"
            disabled={!isConnected}
            onClick={handleReadAll}
          >
            读参数
          </Button>
          <Button
            size="sm"
            colorPalette="brand"
            variant="solid"
            disabled={!isConnected}
            onClick={handleSendAll}
          >
            写参数
          </Button>
        </HStack>
      </Flex>

      <Box as="main" flex={1} overflowY="auto" p={5}>
        <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 4, xl: 5 }} gap={4}>
          {JOINT_SCHEMAS.map((schema) => (
            <JointCard
              key={schema.jointName}
              schema={schema}
              values={allValues.get(schema.jointName) ?? new Map()}
              onChange={(key, value) =>
                handleParamChange(schema.jointName, key, value)
              }
              disabled={!isConnected}
            />
          ))}
        </SimpleGrid>
      </Box>

      <SerialTerminal
        txLog={serial.txLog}
        rxLog={serial.rxLog}
        txBytes={serial.txBytes}
        rxBytes={serial.rxBytes}
      />
    </Box>
  );
}

export default App;
