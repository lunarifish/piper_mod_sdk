import { HStack, NativeSelect, Button, Badge, Box } from '@chakra-ui/react'
import type { ConnectionStatus } from '../hooks/useSerial'

interface ConnectionBarProps {
  status: ConnectionStatus
  ports: string[]
  selectedPort: string
  onSelectPort: (port: string) => void
  onScan: () => void
  onConnect: () => void
  onDisconnect: () => void
}

const STATUS_CONFIG: Record<ConnectionStatus, { label: string; colorPalette: string }> = {
  disconnected: { label: '未连接', colorPalette: 'gray' },
  connecting: { label: '连接中...', colorPalette: 'yellow' },
  connected: { label: '已连接', colorPalette: 'green' },
}

export function ConnectionBar({
  status,
  ports,
  selectedPort,
  onSelectPort,
  onScan,
  onConnect,
  onDisconnect,
}: ConnectionBarProps) {
  const cfg = STATUS_CONFIG[status]
  const isConnected = status === 'connected'
  const isConnecting = status === 'connecting'

  return (
    <HStack gap={2.5} bg="gray.50" px={3} py={1.5} borderRadius="md" borderWidth="1px" borderColor="gray.200">
      <Badge
        variant="subtle"
        colorPalette={cfg.colorPalette}
        size="sm"
        borderRadius="full"
        px={2.5}
        py={0.5}
      >
        <HStack gap={1.5}>
          <Box
            w="6px"
            h="6px"
            borderRadius="full"
            bg={`${cfg.colorPalette}.500`}
            animation={isConnecting ? 'pulse 1.5s infinite' : undefined}
          />
          <Box as="span">{cfg.label}</Box>
        </HStack>
      </Badge>

      <NativeSelect.Root
        size="sm"
        w="220px"
        disabled={isConnected || isConnecting}
      >
        <NativeSelect.Field
          value={selectedPort}
          onChange={(e) => onSelectPort(e.target.value)}
          borderRadius="md"
          cursor={isConnected || isConnecting ? 'not-allowed' : 'pointer'}
        >
          {ports.length === 0 && <option value="">无可用串口 — 请点击「扫描」</option>}
          {ports.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </NativeSelect.Field>
      </NativeSelect.Root>

      <Button
        size="sm"
        variant="outline"
        colorPalette="gray"
        onClick={onScan}
        disabled={isConnected || isConnecting}
      >
        扫描
      </Button>

      {isConnected ? (
        <Button size="sm" colorPalette="red" variant="solid" onClick={onDisconnect}>
          断开
        </Button>
      ) : (
        <Button
          size="sm"
          colorPalette="brand"
          variant="solid"
          onClick={onConnect}
          disabled={isConnecting || ports.length === 0}
        >
          {isConnecting ? '连接中...' : '连接'}
        </Button>
      )}
    </HStack>
  )
}
