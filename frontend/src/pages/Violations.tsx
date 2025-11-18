import { useMemo, useState, useEffect } from 'react'
import { useStore, Violation } from '../store/useStore'
import { Table, Tag, Button } from 'antd'
import ViolationDetailModal from '../components/violations/ViolationDetailModal'
import { confirmViolation, getViolations, skipViolation } from '../services/violations'
import toast from 'react-hot-toast'
import { confirmAction } from '../utils/confirm'
import { downloadCsv } from '../utils/csv'
import ViolationsFilter from '../components/violations/ViolationsFilter'
import { STATUS_TAG_COLOR, getViolationTypes } from '../constants/violations'
import type { ViolationStatus, ViolationType } from '../store/useStore'

export default function Violations() {
  const list = useStore((s) => s.violations)
  const setViolations = useStore((s) => s.setViolations)
  const addOperationLog = useStore((s) => s.addOperationLog)
  const [q, setQ] = useState('')
  const [type, setType] = useState<string>('')
  const [cameraId, setCameraId] = useState<string>('')
  const [status, setStatus] = useState<string>('')
  const [range, setRange] = useState<any>(null)
  const [selected, setSelected] = useState<Violation | null>(null)

  const findLatestViolation = (seed: Violation): Violation | null => {
    const { violations } = useStore.getState()
    if (seed.trackId) {
      const byTrack = violations.find((item) => item.trackId === seed.trackId)
      if (byTrack) return byTrack
    }
    return violations.find((item) => item.id === seed.id) ?? null
  }

  // Map backend violation_tags sang frontend ViolationType
  const mapViolationTypeToFrontend = (backendType: string): ViolationType => {
    const typeMap: Record<string, ViolationType> = {
      detected: 'Phát hiện',
      'stopline_crossing': 'Phát hiện',
      'red_light': 'Vượt đèn đỏ',
      'no_helmet': 'Không đội mũ',
      'speed_violation': 'Quá tốc độ',
    }
    return typeMap[backendType] || 'Phát hiện'
  }

  // Fetch violations từ DB khi mount (chỉ 1 lần) - LẤY TOÀN BỘ, KHÔNG FILTER
  const refreshViolationsFromDB = async () => {
    try {
      // Lấy toàn bộ violations (không filter status, không giới hạn)
      const response = await getViolations({ limit: 10000 }) // Tăng limit để lấy toàn bộ
      const violationsFromAPI: Violation[] = (response.data || []).map((v) => {
        // Chỉ dùng violation_tags
        const rawTags = Array.isArray(v.violation_tags) && v.violation_tags.length
          ? v.violation_tags
          : ['detected']

        const tagLabels = rawTags
          .map(mapViolationTypeToFrontend)
          .filter(Boolean) as ViolationType[]

        const violationHistory = Array.isArray(v.violation_history)
          ? v.violation_history.map((entry) => ({
              type: entry?.type ? mapViolationTypeToFrontend(entry.type) : undefined,
              timestamp: entry?.timestamp,
              speed: entry?.speed,
            }))
          : undefined

        return {
          id: v.id,
          time: v.timestamp,
          cameraId: v.camera_id,
          cameraName: v.camera_name || `Camera ${v.camera_id}`,
          location: v.location || 'Không rõ',
          vehicleType: v.vehicle_type,
          plate: v.license_plate || '',
          confidence: v.confidence,
          trackId: v.track_id,
          speed: v.speed,
          type: tagLabels[0] ?? 'Phát hiện',
          types: tagLabels,
          status: v.status === 'detected' ? 'Mới' : (v.status === 'confirmed' ? 'Đã xác nhận' : 'Đã bỏ qua'),
          images: {
            overview: v.images?.full_frame || '',
            vehicle: v.images?.vehicle_crop || '',
            plate: v.images?.plate_crop || '',
          },
          violationHistory,
        }
      })
      // Cập nhật toàn bộ violations từ DB (đồng bộ với DB) - THAY THẾ hoàn toàn, không merge
      setViolations(violationsFromAPI)
      console.log(`✅ Đã refresh violations từ DB: ${violationsFromAPI.length} violations`)
    } catch (e) {
      console.error('Lỗi fetch violations:', e)
    }
  }

  // Chỉ fetch khi mount (load page)
  useEffect(() => {
    refreshViolationsFromDB()
  }, [setViolations])

  const filtered = useMemo(() => {
    const filtered = list.filter((v) => {
      const labels = getViolationTypes(v)
      const okType = !type || labels.includes(type as ViolationType)
      const okCam = !cameraId || v.cameraId === cameraId
      const okStatus = !status || v.status === status
      const okQ = !q || `${v.plate} ${v.cameraName} ${v.location}`.toLowerCase().includes(q.toLowerCase())
      let okTime = true
      if (range && range[0] && range[1]) {
        const ts = new Date(v.time).getTime()
        const start = (range[0] as any)?.valueOf?.() ?? new Date(range[0]).getTime()
        const end = (range[1] as any)?.valueOf?.() ?? new Date(range[1]).getTime()
        okTime = ts >= start && ts <= end
      }
      return okType && okCam && okStatus && okQ && okTime
    })
    // Sort: mới nhất trên cùng (timestamp giảm dần)
    // Sử dụng localeCompare để đảm bảo sort đúng với string ISO format
    const sorted = filtered.sort((a, b) => {
      const timeA = new Date(a.time).getTime()
      const timeB = new Date(b.time).getTime()
      // Nếu timestamp không hợp lệ, dùng string comparison
      if (isNaN(timeA) || isNaN(timeB)) {
        return b.time.localeCompare(a.time)
      }
      return timeB - timeA // Giảm dần: mới nhất trước
    })
    return sorted
  }, [list, q, type, cameraId, status, range])

  const statusColor = STATUS_TAG_COLOR

  function onDownloadCsv() {
    const header = ['Thời gian','Loại','BSX','Phương tiện','Tốc độ','Camera','Vị trí','Trạng thái']
    const rows = filtered.map(v => [
      new Date(v.time).toLocaleString('vi-VN'),
      getViolationTypes(v).join(', ') || v.type,
      v.plate ?? '',
      v.vehicleType ? (v.vehicleType === 'car' ? 'Ô tô' : v.vehicleType === 'motorcycle' ? 'Xe máy' : v.vehicleType === 'bus' ? 'Xe buýt' : v.vehicleType === 'truck' ? 'Xe tải' : v.vehicleType) : '—',
      typeof v.speed === 'number' ? `${v.speed.toFixed(1)} km/h` : '—',
      v.cameraName,
      v.location,
      v.status
    ])
    downloadCsv('violations.csv', rows, header)
  }

  async function onConfirm(v: Violation, payload?: { types?: ViolationType[]; vehicleType?: string | null; plate?: string | null }): Promise<boolean> {
    const ok = await confirmAction('Xác nhận vi phạm này?')
    if (!ok) return false
    if (!v.trackId) {
      toast.error('Không có track_id để xác nhận')
      return false
    }
    await confirmViolation(v.trackId)
    // Refresh từ DB sau khi confirm để đồng bộ
    await refreshViolationsFromDB()
    const latest = findLatestViolation(v)
    const baseTypes = payload?.types?.length
      ? payload.types
      : (() => {
          const arr = getViolationTypes(v)
          return (arr.length ? arr : [v.type]) as ViolationType[]
        })()
    const payloadHasVehicle = payload ? Object.prototype.hasOwnProperty.call(payload, 'vehicleType') : false
    const payloadHasPlate = payload ? Object.prototype.hasOwnProperty.call(payload, 'plate') : false
    const nextVehicleType = payloadHasVehicle ? (payload?.vehicleType ?? undefined) : v.vehicleType
    const nextPlate = payloadHasPlate ? (payload?.plate ?? '') : v.plate
    const fallback: Violation = {
      ...v,
      status: 'Đã xác nhận',
      types: baseTypes,
      type: baseTypes[0] ?? v.type,
      vehicleType: nextVehicleType,
      plate: nextPlate,
    }
    addOperationLog({
      id: `${v.id}-confirm-${Date.now()}`,
      timestamp: new Date().toISOString(),
      user: '',
      action: 'confirm',
      violationTypes: baseTypes,
      trackId: v.trackId,
      plate: nextPlate,
      camera: v.cameraName,
      details: 'Xác nhận vi phạm'
    })

    // Đóng modal ngay
    setSelected(null)
    return true
  }

  async function onSkip(v: Violation, payload?: { types?: ViolationType[]; vehicleType?: string | null; plate?: string | null }): Promise<boolean> {
    const ok = await confirmAction('Bỏ qua vi phạm này?')
    if (!ok) return false
    if (!v.trackId) {
      toast.error('Không có track_id để bỏ qua')
      return false
    }
    await skipViolation(v.trackId)
    // Refresh từ DB sau khi skip để đồng bộ
    await refreshViolationsFromDB()
    const latest = findLatestViolation(v)
    const baseTypes = payload?.types?.length
      ? payload.types
      : (() => {
          const arr = getViolationTypes(v)
          return (arr.length ? arr : [v.type]) as ViolationType[]
        })()
    const payloadHasVehicle = payload ? Object.prototype.hasOwnProperty.call(payload, 'vehicleType') : false
    const payloadHasPlate = payload ? Object.prototype.hasOwnProperty.call(payload, 'plate') : false
    const nextVehicleType = payloadHasVehicle ? (payload?.vehicleType ?? undefined) : v.vehicleType
    const nextPlate = payloadHasPlate ? (payload?.plate ?? '') : v.plate
    const fallback: Violation = {
      ...v,
      status: 'Đã bỏ qua',
      types: baseTypes,
      type: baseTypes[0] ?? v.type,
      vehicleType: nextVehicleType,
      plate: nextPlate,
    }
    addOperationLog({
      id: `${v.id}-skip-${Date.now()}`,
      timestamp: new Date().toISOString(),
      user: '',
      action: 'skip',
      violationTypes: baseTypes,
      trackId: v.trackId,
      plate: nextPlate,
      camera: v.cameraName,
      details: 'Bỏ qua vi phạm'
    })

    // Đóng modal ngay
    setSelected(null)
    return true
  }

  return (
    <>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>Danh sách</span>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button onClick={refreshViolationsFromDB}>Làm mới</Button>
          <Button onClick={onDownloadCsv}>Tải CSV</Button>
        </div>
      </div>
      <ViolationsFilter
        q={q}
        onQChange={setQ}
        cameraId={cameraId}
        onCameraIdChange={setCameraId}
        type={type}
        onTypeChange={setType}
        status={status}
        onStatusChange={setStatus}
        range={range}
        onRangeChange={setRange}
      />
      <Table
        rowKey="id"
        dataSource={filtered}
        pagination={{ pageSize: 10 }}
        columns={[
          {
            title: 'Thời gian',
            dataIndex: 'time',
            render: (t: string) => new Date(t).toLocaleString('vi-VN'),
          },
          {
            title: 'Loại',
            dataIndex: 'type',
            render: (_: any, record: Violation) => getViolationTypes(record).join(', '),
          },
          { title: 'BSX', dataIndex: 'plate', render: (x: string) => x ?? '—' },
          { title: 'Phương tiện', dataIndex: 'vehicleType', render: (vt: string) => vt ? (vt === 'car' ? 'Ô tô' : vt === 'motorcycle' ? 'Xe máy' : vt === 'bus' ? 'Xe buýt' : vt === 'truck' ? 'Xe tải' : vt) : '—' },
          { title: 'Tốc độ', dataIndex: 'speed', render: (s: number) => typeof s === 'number' ? `${s.toFixed(1)} km/h` : '—' },
          { title: 'Camera', dataIndex: 'cameraName' },
          { title: 'Vị trí', dataIndex: 'location' },
          { title: 'Trạng thái', dataIndex: 'status', render: (s: string) => <Tag color={statusColor[s as ViolationStatus]}>{s === 'Mới' ? 'Chờ duyệt' : s}</Tag> },
          { title: 'Ảnh', dataIndex: ['images', 'vehicle'], render: (_: string, v: Violation) => <a onClick={() => setSelected(v)}>Xem</a> },
        ]}
      />
      <ViolationDetailModal
        open={!!selected}
        onClose={() => setSelected(null)}
        data={selected ?? undefined}
        onConfirm={async (payload) => selected ? await onConfirm(selected, payload) : false}
        onSkip={async (payload) => selected ? await onSkip(selected, payload) : false}
      />
    </>
  )
}
