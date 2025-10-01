import { create } from 'zustand'
import type { CameraRegion } from '../types/regions'

export type ViolationType = 'Vượt đèn đỏ' | 'Không đội mũ' | 'Quá tốc độ'
export type ViolationStatus = 'Mới' | 'Đã xác nhận' | 'Đã bỏ qua'

export interface Violation {
  id: string
  type: ViolationType
  cameraId: string
  cameraName: string
  location: string
  time: string
  speed?: number
  plate?: string
  vehicleType?: string
  confidence: number
  images: {
    overview: string
    vehicle: string
    plate: string
  }
  status: ViolationStatus
}

export interface Settings {
  speedLimit: number
  enableHelmetCheck: boolean
  enableSpeedCheck: boolean
  enableRedLightCheck: boolean
  minConfidence: number
  autoSendZaloOnConfirm: boolean
  zaloToken: string
  zaloTargetId: string
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
  violationType: ViolationType
  plate?: string
  camera: string
  details?: string
}

interface State {
  violations: Violation[]
  addViolation: (v: Violation) => void
  updateViolation: (id: string, patch: Partial<Violation>) => void
  operationLogs: OperationLogEntry[]
  addOperationLog: (entry: OperationLogEntry) => void
  settings: Settings
  updateSettings: (patch: Partial<Settings>) => void
  /** Merge/update a camera's region config */
  setCameraRegion: (cameraId: string, patch: Partial<CameraRegion>) => void
  /** Clear a camera region (target part or all) */
  clearCameraRegion: (cameraId: string, target?: 'stopLine' | 'roi' | 'all') => void
}

const initialSettings: Settings = {
  speedLimit: 60,
  enableHelmetCheck: true,
  enableSpeedCheck: true,
  enableRedLightCheck: true,
  minConfidence: 0.6,
  autoSendZaloOnConfirm: false,
  zaloToken: '',
  zaloTargetId: '',
  cameras: [],
  monitorSelectedCamIds: [],
  monitorShowAll: true,
  monitorFocusedCamId: null,
  monitorPage: 0,
  cameraRegions: {},
}

export const useStore = create<State>((set) => ({
  violations: [],
  addViolation: (v) => set((s) => ({ violations: [v, ...s.violations] })),
  updateViolation: (id, patch) => set((s) => ({
    violations: s.violations.map((x) => (x.id === id ? { ...x, ...patch } : x)),
  })),
  operationLogs: [],
  addOperationLog: (entry) => set((s) => ({
    operationLogs: [entry, ...s.operationLogs].slice(0, 200),
  })),
  settings: initialSettings,
  updateSettings: (patch) => set((s) => ({ settings: { ...s.settings, ...patch } })),
  setCameraRegion: (cameraId, patch) => set((s) => {
    const currentRegions = s.settings.cameraRegions || {}
    const prev = currentRegions[cameraId] || {}
    const next = { ...prev, ...patch }
    return {
      settings: {
        ...s.settings,
        cameraRegions: { ...currentRegions, [cameraId]: next },
      },
    }
  }),
  clearCameraRegion: (cameraId, target) => set((s) => {
    const map = { ...(s.settings.cameraRegions || {}) }
    if (!target || target === 'all') {
      delete map[cameraId]
    } else {
      const prev = map[cameraId]
      if (prev) {
        const updated: CameraRegion = { ...prev }
        if (target === 'stopLine') delete (updated as any).stopLine
        if (target === 'roi') delete (updated as any).roi
        map[cameraId] = updated
      }
    }
    return { settings: { ...s.settings, cameraRegions: map } }
  }),
}))

export const VIOLATION_TYPES: ViolationType[] = ['Vượt đèn đỏ', 'Không đội mũ', 'Quá tốc độ']

