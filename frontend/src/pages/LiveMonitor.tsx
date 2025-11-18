import { useCallback, useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { Row, Col, Space, Select, Button, Grid, Card, Pagination } from 'antd'
import { useStore, Violation, ViolationType } from '../store/useStore'
import { listCameras, getCameraDensity } from '../services/camera.service'
import { confirmViolation, skipViolation, getViolations } from '../services/violations'
import { getViolationTypes } from '../constants/violations'
import ViolationDetailModal from '../components/violations/ViolationDetailModal'
import CameraTile from '../components/CameraTile'
import OperationLog from '../components/OperationLog'
import ViolationList from '../components/violations/ViolationList'
import SectionHeader from '../components/SectionHeader'
import { confirmAction } from '../utils/confirm'
import { config } from '../config'

type ConfirmPayload = { types?: ViolationType[]; vehicleType?: string | null; plate?: string | null }

export default function LiveMonitor() {
  const settings = useStore((s) => s.settings)
  const { cameras } = settings
  const violations = useStore((s) => s.violations)
  const updateViolation = useStore((s) => s.updateViolation)
  const updateSettings = useStore((s) => s.updateSettings)
  const [selected, setSelected] = useState<Violation | null>(null)
  const [modalReadOnly, setModalReadOnly] = useState(false)

  // Khôi phục trạng thái UI từ store
  const [showAll, setShowAll] = useState(settings.monitorShowAll)
  const [selectedCamIds, setSelectedCamIds] = useState<string[]>(settings.monitorSelectedCamIds)
  const [focusedCamId, setFocusedCamId] = useState<string | null>(settings.monitorFocusedCamId)
  const [currentPage, setCurrentPage] = useState(settings.monitorPage)

  const findLatestViolation = useCallback((seed: Violation): Violation | null => {
    const { violations: all } = useStore.getState()
    if (seed.trackId) {
      const byTrack = all.find((item) => item.trackId === seed.trackId)
      if (byTrack) return byTrack
    }
    return all.find((item) => item.id === seed.id) ?? null
  }, [])

  // State lưu vehicle density cho mỗi camera
  const [vehicleDensities, setVehicleDensities] = useState<Record<string, number>>({})

  // Lưu trạng thái UI khi thay đổi
  useEffect(() => {
    updateSettings({
      monitorShowAll: showAll,
      monitorSelectedCamIds: selectedCamIds,
      monitorFocusedCamId: focusedCamId,
      monitorPage: currentPage,
    })
  }, [showAll, selectedCamIds, focusedCamId, currentPage, updateSettings])

const fetchCameras = useCallback(async () => {
  try {
    const list = await listCameras()
    const cams = (list || []).map((c) => ({ id: c.id, name: c.name, rtsp: c.rtsp, location: c.location }))
    const regionsMap: any = {}
    for (const cam of list || []) {
      if (cam.regions) regionsMap[cam.id] = cam.regions
    }
    updateSettings({ cameras: cams, cameraRegions: regionsMap })
  } catch (error) {
    console.error('Lỗi tải danh sách camera:', error)
  }
}, [updateSettings])

useEffect(() => {
  void fetchCameras()
}, [fetchCameras])

  // Lắng nghe SSE camera events để làm tươi ngay khi có thay đổi
useEffect(() => {
  if (typeof window === 'undefined') return
  const timer = window.setInterval(() => {
    void fetchCameras()
  }, config.polling.cameras)
  return () => window.clearInterval(timer)
}, [fetchCameras])

  // Fetch violations từ DB và tự động refresh để hiển thị violations mới (không cần click)
  const setViolations = useStore((s) => s.setViolations)

  const refreshViolationsFromDB = async () => {
    try {
      // Chỉ lấy violations chưa xử lý (status = detected)
      const response = await getViolations({ limit: 100, status: 'detected' })

      // Map backend violation_tags to frontend type
      const mapViolationType = (backendType: string): ViolationType => {
        const typeMap: Record<string, ViolationType> = {
          detected: 'Phát hiện',
          'stopline_crossing': 'Phát hiện',
          'red_light': 'Vượt đèn đỏ',
          'no_helmet': 'Không đội mũ',
          'speed_violation': 'Quá tốc độ',
        }
        return typeMap[backendType] || 'Phát hiện'
      }

      const violationsFromAPI: Violation[] = (response.data || []).map((v) => {
        // Chỉ dùng violation_tags
        const rawTags = Array.isArray(v.violation_tags) && v.violation_tags.length
          ? v.violation_tags
          : ['detected']

        const tagLabels = rawTags
          .map(mapViolationType)
          .filter(Boolean) as ViolationType[]

        const violationHistory = Array.isArray(v.violation_history)
          ? v.violation_history.map((entry) => ({
              type: entry?.type ? mapViolationType(entry.type) : undefined,
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
          status: 'Mới',
          images: {
            overview: v.images?.full_frame || '',
            vehicle: v.images?.vehicle_crop || '',
            plate: v.images?.plate_crop || '',
          },
          violationHistory,
        }
      })

      // Đồng bộ với DB: chỉ giữ lại violations đã confirm/skip, thay thế toàn bộ violations 'Mới'
      const currentViolations = useStore.getState().violations
      const existingConfirmed = currentViolations.filter(v => v.status !== 'Mới')
      setViolations([...existingConfirmed, ...violationsFromAPI])
    } catch (e) {
      console.error('Lỗi fetch violations:', e)
    }
  }

  useEffect(() => {
    // Fetch khi mount
    refreshViolationsFromDB()

    // Tự động refresh mỗi 5 giây để hiển thị violations mới (không cần click)
    const interval = setInterval(refreshViolationsFromDB, 5000)
    return () => clearInterval(interval)
  }, [setViolations])
  // Poll vehicle density từ backend mỗi 2 giây
  useEffect(() => {
    if (!cameras || cameras.length === 0) return

    const fetchDensities = async () => {
      const densities: Record<string, number> = {}
      for (const cam of cameras) {
        try {
          const info = await getCameraDensity(cam.rtsp)
          densities[cam.id] = info.count
        } catch {
          densities[cam.id] = 0
        }
      }
      setVehicleDensities(densities)
    }

    fetchDensities() // Gọi ngay lần đầu
    const interval = setInterval(fetchDensities, 2000) // Poll mỗi 2 giây
    return () => clearInterval(interval)
  }, [cameras])

  const [filter, setFilter] = useState<'Tất cả' | ViolationType>('Tất cả')
  const pendingList = useMemo(() => {
    const filtered = violations.filter(v => v.status === 'Mới')
    // Sort: mới nhất trên cùng (timestamp giảm dần)
    const sorted = filtered.sort((a, b) => {
      const timeA = new Date(a.time).getTime()
      const timeB = new Date(b.time).getTime()
      // Nếu timestamp không hợp lệ, dùng string comparison
      if (isNaN(timeA) || isNaN(timeB)) {
        return b.time.localeCompare(a.time)
      }
      return timeB - timeA // Giảm dần: mới nhất trước
    })
    return sorted.slice(0, 50)
  }, [violations])
  const filtered = useMemo(() => (
    filter === 'Tất cả'
      ? pendingList
      : pendingList.filter((v) => getViolationTypes(v).includes(filter))
  ), [pendingList, filter])
  const screens = Grid.useBreakpoint()
  const isMobile = !screens.md

  const counts = useMemo(() => {
    const pending = violations.filter(v => v.status === 'Mới')
    const total = pending.length
    const red = pending.filter(v => getViolationTypes(v).includes('Vượt đèn đỏ')).length
    const speed = pending.filter(v => getViolationTypes(v).includes('Quá tốc độ')).length
    const helmet = pending.filter(v => getViolationTypes(v).includes('Không đội mũ')).length
    return { total, red, speed, helmet }
  }, [violations])

  async function onConfirm(v: Violation, payload?: ConfirmPayload): Promise<boolean> {
    const ok = await confirmAction('Xác nhận vi phạm này?')
    if (!ok) return false
    if (!v.trackId) {
      toast.error('Không có track_id để xác nhận')
      return false
    }
    const updatedTypes = (payload?.types && payload.types.length
      ? payload.types
      : (() => {
          const arr = getViolationTypes(v)
          return (arr.length ? arr : [v.type]) as ViolationType[]
        })())
    const payloadHasVehicle = payload ? Object.prototype.hasOwnProperty.call(payload, 'vehicleType') : false
    const payloadHasPlate = payload ? Object.prototype.hasOwnProperty.call(payload, 'plate') : false
    const updatedVehicleType = payloadHasVehicle ? (payload?.vehicleType ?? undefined) : v.vehicleType
    const updatedPlate = payloadHasPlate ? (payload?.plate ?? '') : v.plate
    updateViolation(v.id, {
      status: 'Đã xác nhận',
      types: updatedTypes,
      type: updatedTypes[0] ?? v.type,
      vehicleType: updatedVehicleType,
      plate: updatedPlate,
    })
    await confirmViolation(v.trackId)
    // Refresh violations từ DB sau khi confirm
    await refreshViolationsFromDB()

    // Cập nhật local state ngay lập tức
    updateViolation(v.id, {
      status: 'Đã xác nhận',
      types: updatedTypes,
      type: updatedTypes[0] ?? v.type,
      vehicleType: updatedVehicleType,
      plate: updatedPlate,
    })

    // Đóng modal ngay sau khi xác nhận thành công
    setSelected(null)
    useStore.getState().addOperationLog({
      id: `${v.id}-confirm-${Date.now()}`,
      timestamp: new Date().toISOString(),
      user: '',
      action: 'confirm',
      violationTypes: updatedTypes as ViolationType[],
      trackId: v.trackId,
      plate: updatedPlate,
      camera: v.cameraName,
      details: 'Xác nhận vi phạm'
    })
    return true
  }

  async function onSkip(v: Violation, payload?: ConfirmPayload): Promise<boolean> {
    const ok = await confirmAction('Bỏ qua vi phạm này?')
    if (!ok) return false
    if (!v.trackId) {
      toast.error('Không có track_id để bỏ qua')
      return false
    }
    const updatedTypes = (payload?.types && payload.types.length
      ? payload.types
      : (() => {
          const arr = getViolationTypes(v)
          return (arr.length ? arr : [v.type]) as ViolationType[]
        })())
    const payloadHasVehicle = payload ? Object.prototype.hasOwnProperty.call(payload, 'vehicleType') : false
    const payloadHasPlate = payload ? Object.prototype.hasOwnProperty.call(payload, 'plate') : false
    const updatedVehicleType = payloadHasVehicle ? (payload?.vehicleType ?? undefined) : v.vehicleType
    const updatedPlate = payloadHasPlate ? (payload?.plate ?? '') : v.plate
    updateViolation(v.id, {
      status: 'Đã bỏ qua',
      types: updatedTypes,
      type: updatedTypes[0] ?? v.type,
      vehicleType: updatedVehicleType,
      plate: updatedPlate,
    })
    await skipViolation(v.trackId)
    // Refresh violations từ DB sau khi skip
    await refreshViolationsFromDB()

    // Cập nhật local state ngay lập tức
    updateViolation(v.id, {
      status: 'Đã bỏ qua',
      types: updatedTypes,
      type: updatedTypes[0] ?? v.type,
      vehicleType: updatedVehicleType,
      plate: updatedPlate,
    })

    // Đóng modal ngay sau khi bỏ qua thành công
    setSelected(null)
    useStore.getState().addOperationLog({
      id: `${v.id}-skip-${Date.now()}`,
      timestamp: new Date().toISOString(),
      user: '',
      action: 'skip',
      violationTypes: updatedTypes as ViolationType[],
      trackId: v.trackId,
      plate: updatedPlate,
      camera: v.cameraName,
      details: 'Bỏ qua vi phạm'
    })
    return true
  }



  // Pagination cho camera khi có quá nhiều
  const CAMERAS_PER_PAGE = 6 // Tối đa 6 camera (2 hàng x 3 cột)

  const { allCams, totalPages } = useMemo(() => {
    let cams: typeof cameras = []
    if (focusedCamId) {
      const cam = cameras.find((c) => c.id === focusedCamId)
      cams = cam ? [cam] : []
    } else if (selectedCamIds.length > 0) {
      cams = cameras.filter((c) => selectedCamIds.includes(c.id))
    } else {
      cams = showAll ? cameras : cameras
    }

    // Dedupe by id to avoid duplicate tiles due to transient UI states
    const uniq = Array.from(new Map(cams.map((c) => [c.id, c])).values())

    const pages = Math.max(1, Math.ceil(uniq.length / CAMERAS_PER_PAGE))
    return { allCams: uniq, totalPages: pages }
  }, [cameras, selectedCamIds, showAll, focusedCamId])

  // Đảm bảo trang hiện tại luôn hợp lệ khi số lượng camera thay đổi
  useEffect(() => {
    if (currentPage > 0 && currentPage >= totalPages) {
      setCurrentPage(Math.max(0, totalPages - 1))
    }
  }, [totalPages, currentPage])

  // Nếu đang focus vào cam không tồn tại nữa → bỏ focus
  useEffect(() => {
    if (focusedCamId && !cameras.find(c => c.id === focusedCamId)) {
      setFocusedCamId(null)
    }
  }, [cameras, focusedCamId])

  // Làm sạch danh sách chọn nếu có ID không còn tồn tại
  useEffect(() => {
    if (selectedCamIds.length > 0) {
      const validIds = new Set(cameras.map(c => c.id))
      const filtered = selectedCamIds.filter(id => validIds.has(id))
      if (filtered.length !== selectedCamIds.length) {
        setSelectedCamIds(filtered)
      }
    }
  }, [cameras, selectedCamIds])

  const displayCams = useMemo(() => {
    const start = currentPage * CAMERAS_PER_PAGE
    return allCams.slice(start, start + CAMERAS_PER_PAGE)
  }, [allCams, currentPage])

  // Bố cục: full khi focus 1 cam, grid 3 cột khi nhiều cam
  const camSpan = useMemo(() => {
    if (focusedCamId) return { xs: 24, sm: 24, md: 24, lg: 24 } // Full width khi focus
    return { xs: 24, sm: 12, md: 8, lg: 8 } // 3 cột khi grid
  }, [focusedCamId])
  const camHeight = 'auto' // Để CSS aspect-ratio 16:9 tự xử lý

  const panelHeight = isMobile ? undefined : '84vh'

  return (
    <Row gutter={16}>
      <Col xs={24} lg={16}>
        <SectionHeader
          title="Luồng camera"
          extra={
            focusedCamId ? (
              <Button onClick={() => setFocusedCamId(null)}>Thoát phóng to</Button>
            ) : (
              <Space>
                <Select
                  mode="multiple"
                  allowClear
                  value={selectedCamIds}
                  onChange={(vals) => {
                    setSelectedCamIds(vals)
                    if (vals.length > 0) setShowAll(false)
                  }}
                  placeholder="Chọn camera hiển thị"
                  style={{ minWidth: 260 }}
                  options={cameras.map((c) => ({ value: c.id, label: `${c.name} — ${c.location}` }))}
                />
                <Button onClick={() => { setSelectedCamIds([]); setShowAll(true) }} disabled={showAll && selectedCamIds.length === 0}>
                  Hiển thị tất cả cam
                </Button>
              </Space>
            )
          }
        />
        <div style={{ height: panelHeight ?? 'auto', display: 'flex', flexDirection: 'column', gap: 12, minHeight: 0 }}>
          <Card style={{ flex: 1 }} bodyStyle={{ height: panelHeight ? '100%' : 'auto', overflow: 'auto', padding: 10 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, height: '100%' }}>
              <Row gutter={[12,12]} style={{ flex: 1 }}>
                {displayCams.map(cam => (
                  <Col key={cam.id} {...camSpan}>
                    <CameraTile
                      cameraId={cam.id}
                      name={cam.name}
                      location={cam.location}
                      rtsp={cam.rtsp}
                      vehicleDensity={vehicleDensities[cam.id] ?? 0}
                      onDoubleClick={() => {
                        setFocusedCamId((prev) => (prev === cam.id ? null : cam.id))
                        setCurrentPage(0) // Reset về trang đầu khi focus/unfocus
                      }}
                      focused={focusedCamId === cam.id}
                    />
                  </Col>
                ))}
              </Row>
              {/* Pagination thay thế thanh cuộn */}
              {totalPages > 1 && !focusedCamId && (
                <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 8 }}>
                  <Pagination
                    simple
                    current={currentPage + 1}
                    total={allCams.length}
                    pageSize={CAMERAS_PER_PAGE}
                    onChange={(page) => setCurrentPage(page - 1)}
                    showSizeChanger={false}
                  />
                </div>
              )}
            </div>
          </Card>

          {/* Nhật ký thao tác */}
          <div style={{ height: '200px' }}>
            <OperationLog onSelect={({ trackId, plate, violationTypes, camera }) => {
              const allViolations = useStore.getState().violations
              let candidate: Violation | undefined
              if (trackId) {
                candidate = allViolations.find((item) => item.trackId === trackId)
              }
              if (!candidate && plate) {
                candidate = allViolations.find((item) => item.plate && item.plate === plate)
              }
              const requested = violationTypes && violationTypes.length ? new Set(violationTypes) : undefined
              if (!candidate && requested) {
                candidate = allViolations.find((item) => {
                  const labels = getViolationTypes(item)
                  const matchType = labels.some((label) => requested.has(label))
                  return matchType && (!camera || item.cameraName === camera)
                })
              }
              if (!candidate && requested) {
                candidate = pendingList.find((item) => getViolationTypes(item).some((label) => requested.has(label)))
              }
              if (!candidate) {
                candidate = pendingList[0] ?? allViolations.find((item) => item.status === 'Mới')
              }
              setSelected(candidate ? { ...candidate } : null)
              setModalReadOnly(candidate ? candidate.status !== 'Mới' : true)
            }} />
          </div>
        </div>
      </Col>
      <Col xs={24} lg={8}>
        <div style={{ height: panelHeight ?? 'auto', display: 'flex', flexDirection: 'column', gap: 12, minHeight: 0 }}>
          {/* Phần lọc mới với design đẹp hơn */}
          <div className="violation-filter-panel">
            <div className="filter-header">
              <span className="filter-title">Vi phạm giao thông</span>
              <span className="filter-count">{filtered.length} mục</span>
            </div>
            <div className="filter-tabs">
              <div
                className={`filter-tab ${filter === 'Tất cả' ? 'active' : ''}`}
                onClick={() => setFilter('Tất cả')}
              >
                <span className="tab-label">Tất cả</span>
                <span className="tab-count">{counts.total}</span>
              </div>
              <div
                className={`filter-tab red ${filter === 'Vượt đèn đỏ' ? 'active' : ''}`}
                onClick={() => setFilter('Vượt đèn đỏ')}
              >
                <span className="tab-label">Vượt đèn đỏ</span>
                <span className="tab-count">{counts.red}</span>
              </div>
              <div
                className={`filter-tab cyan ${filter === 'Quá tốc độ' ? 'active' : ''}`}
                onClick={() => setFilter('Quá tốc độ')}
              >
                <span className="tab-label">Quá tốc độ</span>
                <span className="tab-count">{counts.speed}</span>
              </div>
              <div
                className={`filter-tab gold ${filter === 'Không đội mũ' ? 'active' : ''}`}
                onClick={() => setFilter('Không đội mũ')}
              >
                <span className="tab-label">Không đội mũ</span>
                <span className="tab-count">{counts.helmet}</span>
              </div>
            </div>
          </div>
          <div style={{ flex: 1, minHeight: 0 }}>
            <ViolationList items={filtered} onClick={(v) => { setSelected(v); setModalReadOnly(false) }} height={panelHeight ? '100%' : undefined} />
          </div>
        </div>
      </Col>

      <ViolationDetailModal
        open={!!selected}
        onClose={() => setSelected(null)}
        data={selected ?? undefined}
        onConfirm={async (payload) => (selected ? await onConfirm(selected, payload) : false)}
        onSkip={async (payload) => (selected ? await onSkip(selected, payload) : false)}
        readOnly={modalReadOnly}
      />
    </Row>
  )
}
