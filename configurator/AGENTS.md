# Swerve Configurator

Web-based parameter configurator for a 5-joint robotic arm, communicating via serial port.

## Tech Stack

- **React 19** + **TypeScript 6** + **Chakra UI v3** (custom theme)
- **Vite 8** for dev/build
- **Web Serial API** — Chromium-based browsers only (Chrome/Edge/Opera)

## Quick Start

```bash
cd configurator
npm install
npm run dev      # → http://localhost:5173
npm run build    # production build → dist/
```

## Project Structure

```
src/
├── main.tsx                   # Entry: wraps App in ChakraProvider with custom theme
├── App.tsx                    # Root: layout, state, handlers (send/read all)
├── theme.ts                   # Chakra v3 system theme — brand blue palette
├── components/
│   ├── ConnectionBar.tsx       # Serial port scan/connect/disconnect + status badge
│   ├── JointCard.tsx           # One card per joint, colored accent bar per joint
│   ├── ParamSlider.tsx         # Slider + NumberInput for one parameter
│   ├── SerialTerminal.tsx      # Footer: hex dump viewer (TX/RX logs)
│   └── ui/
│       └── toaster.tsx         # Toast notification system
├── hooks/
│   └── useSerial.ts           # Web Serial API wrapper (921600 8N1)
└── schemas/
    └── params.ts              # Joint/param definitions (J1–J5, 5 params each)
```

## Architecture: Data Flow

```
App.tsx  (owner of allValues: Map<jointName, Map<paramKey, value>>)
  ├── ConnectionBar ──► useSerial ──► Web Serial API
  ├── SimpleGrid of JointCard[] ──► ParamSlider[] ── onChange → handleParamChange
  └── SerialTerminal  ◄── txLog/rxLog/txBytes/rxBytes
```

**State is schema-driven**: `JOINT_SCHEMAS` in `schemas/params.ts` defines joints and their params. The UI renders automatically from it. Adding a param = adding one entry to the schema array.

## Key Types

```typescript
type ConnectionStatus = 'disconnected' | 'connecting' | 'connected'

interface ParamDef {
  key: string; label: string; type: ParamType;
  min?: number; max?: number; step?: number; unit?: string;
  defaultValue: number;
}

interface JointSchema {
  jointName: string;     // "J1"–"J5"
  params: ParamDef[];    // each joint has 5 params
}

interface ByteLogEntry {
  ts: number;            // millisecond timestamp
  data: Uint8Array;      // raw bytes
}
```

## How to Extend

**Add a new parameter** → `schemas/params.ts`: add `ParamDef` to a joint's `params[]`. UI renders automatically.

**Add a new joint (e.g. J6)** → `schemas/params.ts`: add `JointSchema`. Add color to `JOINT_COLORS` in `JointCard.tsx`.

**Add a new param type** (dropdown, toggle, etc.) → extend `ParamType` in `schemas/params.ts`, add rendering branch in `ParamSlider.tsx`.

## Serial Protocol — ⚠️ STUB ONLY

`useSerial.ts` implements Web Serial connection (921600 8N1) with background read loop and TX/RX logging. **The actual protocol frames are not implemented yet:**

- `sendAllParams()` — collects `{joint, key, value}` into an array, logs intent, returns `false` (frame = 0 bytes)
- `readAllParams()` — logs intent, returns `null`

MCU protocol is pending. When ready, implement frame packing/unpacking in these two functions. See source comments for TODO markers.

## UI Conventions

- **Chakra v3** with custom `system` theme defined in `theme.ts` (brand blue `600` as primary)
- Light theme throughout (`bg="white"`, `bg="gray.50"`)
- Joint cards use accent color bars: blue / teal / purple / orange / pink (indexed by joint number)
- All interactive controls disable when not connected
- Toast notifications for async operation feedback (success/error/warning)
- Responsive grid: 1 column on mobile, up to 5 on wide screens
