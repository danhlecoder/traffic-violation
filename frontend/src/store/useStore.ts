import { create } from 'zustand'
import type { CameraRegion } from '../types/regions'

export type ViolationType = 'Phát hiện' | 'Vượt đèn đỏ' | 'Không đội mũ' | 'Quá tốc độ'
export type ViolationStatus = 'Mới' | 'Đã xác nhận' | 'Đã bỏ qua'

export interface Violation {
  id: string
  type: ViolationType
  types?: string[]
  cameraId: string
  cameraName: string
  location: string
  time: string
  speed?: number
  plate?: string
  vehicleType?: string
  confidence: number
  trackId?: string  // Track ID từ backend (string format: 5 ký tự alphanumeric + hhmmss)
  images: {
    overview: string
    vehicle: string
    plate: string
  }
  status: ViolationStatus
  violationHistory?: Array<{
    type?: string
    timestamp?: string
    speed?: number
  }>
}

export interface Settings {
  speedLimit: number
  enableHelmetCheck: boolean
  enableSpeedCheck: boolean
  enableRedLightCheck: boolean
  minConfidence: number
  cameras: Array<{ id: string; name: string; rtsp: string; location: string }>
  // Trạng thái UI cần lưu cho LiveMonitor
  monitorSelectedCamIds: string[]
  monitorShowAll: boolean
  monitorFocusedCamId: string | null
  monitorPage: number
  /** Per-camera drawing regions for red-light line and traffic-light ROI */
  cameraRegions: Record<string, CameraRegion>
}

export interface OperationLogEntry {
  id: string
  timestamp: string
  user: string
  action: 'confirm' | 'skip'
  violationTypes: ViolationType[]
  trackId?: string
  plate?: string
  camera: string
  details?: string
}

interface State {
  violations: Violation[]
  addViolation: (v: Violation) => void
  setViolations: (violations: Violation[]) => void
  updateViolation: (id: string, patch: Partial<Violation>) => void
  operationLogs: OperationLogEntry[]
  addOperationLog: (entry: OperationLogEntry) => void
  settings: Settings
  updateSettings: (patch: Partial<Settings>) => void
  /** Merge/update a camera's region config */
  setCameraRegion: (cameraId: string, patch: Partial<CameraRegion>) => void
  /** Clear a camera region (target part or all) */
  clearCameraRegion: (cameraId: string, target?: 'stopLine' | 'all') => void
}

// Ghi chú: cấu hình mặc định cho ứng dụng (sẽ được merge với cấu hình đã lưu trong localStorage)
const initialSettings: Settings = {
  speedLimit: 60,
  enableHelmetCheck: true,
  enableSpeedCheck: true,
  enableRedLightCheck: true,
  minConfidence: 0.6,
  cameras: [],
  monitorSelectedCamIds: [],
  monitorShowAll: true,
  monitorFocusedCamId: null,
  monitorPage: 0,
  cameraRegions: {},
}

// Tải cấu hình đã lưu từ localStorage (nếu có) và hợp nhất với mặc định
function loadPersistedSettings(): Settings {
  try {
    if (typeof window === 'undefined') return initialSettings
    const raw = localStorage.getItem('tv-settings')
    if (!raw) return initialSettings
    const parsed = JSON.parse(raw)
    // Merge nông để tránh mất field mới thêm
    return { ...initialSettings, ...parsed, cameraRegions: parsed?.cameraRegions || {} }
  } catch {
    return initialSettings
  }
}

export const useStore = create<State>((set) => ({
  violations: [],
  addViolation: (v) => set((s) => {
    // Check duplicate by ID
    if (s.violations.some(existing => existing.id === v.id)) {
      return s // Skip nếu đã tồn tại
    }
    return { violations: [v, ...s.violations] }
  }),
  setViolations: (violations) => set({ violations }),
  updateViolation: (id, patch) => set((s) => ({
    violations: s.violations.map((x) => {
      if (x.id !== id) return x
      const next = { ...x, ...patch }
      if (Array.isArray((patch as any)?.violationTags)) {
        next.types = (patch as any).violationTags as string[]
      }
      return next
    }),
  })),
  operationLogs: [],
  addOperationLog: (entry) => set((s) => ({
    operationLogs: [entry, ...s.operationLogs].slice(0, 200),
  })),
  // Khởi tạo settings từ localStorage nếu có
  settings: loadPersistedSettings(),
  // Cập nhật settings và đồng thời lưu xuống localStorage để giữ lại sau khi refresh
  updateSettings: (patch) => set((s) => {
    const next = { ...s.settings, ...patch }
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem('tv-settings', JSON.stringify(next))
      }
    } catch {}
    return { settings: next }
  }),
  setCameraRegion: (cameraId, patch) => set((s) => {
    const currentRegions = s.settings.cameraRegions || {}
    const prev = currentRegions[cameraId] || {}
    const next = { ...prev, ...patch }
    const settings = {
      ...s.settings,
      cameraRegions: { ...currentRegions, [cameraId]: next },
    }
    // Lưu lại cấu hình sau khi cập nhật vùng vẽ
    try { if (typeof window !== 'undefined') localStorage.setItem('tv-settings', JSON.stringify(settings)) } catch {}
    return { settings }
  }),
  clearCameraRegion: (cameraId, target) => set((s) => {
    const map = { ...(s.settings.cameraRegions || {}) }
    if (!target || target === 'all') {
      delete map[cameraId]
    } else {
      const prev = map[cameraId]
      if (prev) {
        const updated: CameraRegion = { ...prev }
        if (target === 'stopLine') {
          delete (updated as any).stopLine
          delete (updated as any).lineB
        }
        map[cameraId] = updated
      }
    }
    const settings = { ...s.settings, cameraRegions: map }
    try { if (typeof window !== 'undefined') localStorage.setItem('tv-settings', JSON.stringify(settings)) } catch {}
    return { settings }
  }),
}))

export const VIOLATION_TYPES: ViolationType[] = ['Phát hiện', 'Vượt đèn đỏ', 'Không đội mũ', 'Quá tốc độ']
