# Frontend Architecture

## 📁 Cấu trúc Clean Code

```
src/
├── config/              # Configuration
│   └── index.ts         # App config, API base, constants
│
├── services/            # API Services Layer
│   ├── api-client.ts    # HTTP client với error handling
│   ├── camera.service.ts # Camera API
│   ├── violations.ts    # Violation API
│   ├── zalo.ts          # Zalo integration
│   └── streams.ts       # DEPRECATED - use camera.service.ts
│
├── types/               # TypeScript Types
│   ├── api.ts           # API DTOs
│   └── regions.ts       # Region drawing types
│
├── hooks/               # Custom React Hooks
│   ├── useCameras.ts    # Manage cameras data
│   ├── useVehicleDensity.ts # Poll vehicle density
│   ├── useElementScaler.ts  # Canvas scaling
│   └── useRegionDrawing.ts  # Region drawing logic
│
├── components/          # UI Components
│   ├── CameraTile.tsx
│   ├── Layout.tsx
│   ├── charts/
│   └── violations/
│
├── pages/               # Page Components
│   ├── LiveMonitor.tsx
│   ├── Violations.tsx
│   ├── Reports.tsx
│   └── Settings.tsx
│
├── store/               # State Management
│   ├── useStore.ts      # Zustand store
│   └── useTheme.ts      # Theme state
│
└── utils/               # Utilities
    ├── confirm.ts       # Confirmation dialogs
    ├── csv.ts           # CSV export
    └── media.ts         # Media utilities
```

## 🔧 Core Modules

### 1. **config/index.ts** - Configuration
```typescript
import { config } from '@/config'

// API base URL
config.apiBase

// Polling intervals
config.polling.density
config.polling.cameras

// Pagination
config.pagination.defaultPageSize
```

### 2. **services/api-client.ts** - HTTP Client
```typescript
import { apiClient, ApiError } from '@/services/api-client'

// GET request
const data = await apiClient.get<T>('/api/endpoint')

// POST request
await apiClient.post('/api/endpoint', { data })

// Error handling
try {
  await apiClient.get('/api/endpoint')
} catch (error) {
  if (error instanceof ApiError) {
    console.log(error.status, error.message)
  }
}
```

### 3. **services/camera.service.ts** - Camera API
```typescript
import {
  listCameras,
  getCamera,
  upsertCamera,
  deleteCamera,
  getCameraDensity,
  getStreamUrl
} from '@/services/camera.service'

// List all cameras
const cameras = await listCameras()

// Get stream URL
const url = getStreamUrl(rtsp)

// Get vehicle density
const density = await getCameraDensity(rtsp)
```

### 4. **hooks/useCameras.ts** - Camera Hook
```typescript
import { useCameras } from '@/hooks/useCameras'

function MyComponent() {
  const { cameras, loading, error, reload } = useCameras()
  
  // cameras: Camera[]
  // loading: boolean
  // error: Error | null
  // reload: () => Promise<void>
}
```

### 5. **hooks/useVehicleDensity.ts** - Density Hook
```typescript
import { useVehicleDensity } from '@/hooks/useVehicleDensity'

function MyComponent({ rtsp }: { rtsp: string }) {
  const { density, loading } = useVehicleDensity(rtsp)
  
  // Auto-polls every 2s
  // density: number
  // loading: boolean
}
```

## 🎯 Design Principles

### 1. **Separation of Concerns**
- ✅ **Services**: API calls only
- ✅ **Hooks**: Data fetching + state
- ✅ **Components**: UI rendering only
- ✅ **Utils**: Pure functions

### 2. **Reusability**
```typescript
// ❌ BAD: Logic in component
function MyComponent() {
  const [data, setData] = useState([])
  
  useEffect(() => {
    fetch('/api/cameras')
      .then(r => r.json())
      .then(setData)
  }, [])
}

// ✅ GOOD: Reusable hook
function MyComponent() {
  const { cameras } = useCameras()
}
```

### 3. **Type Safety**
```typescript
// ✅ All API responses have types
import type { Camera, VehicleDensity } from '@/types/api'

// ✅ Service functions return typed data
const cameras: Camera[] = await listCameras()
const density: VehicleDensity = await getCameraDensity(rtsp)
```

### 4. **Error Handling**
```typescript
// ✅ Centralized error handling in API client
try {
  await upsertCamera(camera)
} catch (error) {
  if (error instanceof ApiError) {
    toast.error(error.message)
  }
}
```

### 5. **Configuration**
```typescript
// ✅ Centralized config
import { config } from '@/config'

// ❌ Don't hardcode
const url = 'http://localhost:8000/api/cameras'

// ✅ Use config
const url = `${config.apiBase}/api/cameras`
```

## 🔄 Migration Guide

### Old Code → New Code

**Camera API:**
```typescript
// OLD
import { streams } from '@/services/api'
const cameras = await streams.listCameras()

// NEW
import { listCameras } from '@/services/camera.service'
const cameras = await listCameras()
```

**Stream URL:**
```typescript
// OLD
import { streams } from '@/services/api'
const url = streams.buildStreamUrl(rtsp)

// NEW
import { getStreamUrl } from '@/services/camera.service'
const url = getStreamUrl(rtsp)
```

**Types:**
```typescript
// OLD
import type { CameraDto } from '@/services/streams'

// NEW
import type { Camera } from '@/types/api'
```

## 📝 Best Practices

### 1. **Always use services for API calls**
```typescript
// ❌ DON'T fetch directly in components
fetch('/api/cameras').then(...)

// ✅ DO use services
import { listCameras } from '@/services/camera.service'
await listCameras()
```

### 2. **Use custom hooks for data fetching**
```typescript
// ❌ DON'T repeat useEffect logic
function MyComponent() {
  const [cameras, setCameras] = useState([])
  useEffect(() => {
    listCameras().then(setCameras)
  }, [])
}

// ✅ DO use custom hooks
function MyComponent() {
  const { cameras } = useCameras()
}
```

### 3. **Keep components small and focused**
- Max 200 lines per component
- Extract logic to hooks
- Extract repeated JSX to sub-components

### 4. **Use TypeScript properly**
```typescript
// ✅ Type props
interface Props {
  camera: Camera
  onDelete: (id: string) => void
}

// ✅ Type state
const [cameras, setCameras] = useState<Camera[]>([])

// ✅ Type async functions
async function loadData(): Promise<Camera[]> {
  return await listCameras()
}
```

## 🚀 Development

```bash
# Install dependencies
npm install

# Dev server
npm run dev

# Build
npm run build

# Type check
npm run type-check
```

## 📚 Further Reading

- [React Best Practices](https://react.dev/learn)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Clean Code JavaScript](https://github.com/ryanmcdermott/clean-code-javascript)
