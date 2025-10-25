import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { Row, Col, Space, Select, Button, Grid, Card, Pagination } from 'antd'
import { useStore, VIOLATION_TYPES, Violation, ViolationType } from '../store/useStore'
import { streams } from '../services/api'
import { confirmViolation, skipViolation, getViolations } from '../services/violations'
import { sendZalo } from '../services/zalo'
import ViolationDetailModal from '../components/violations/ViolationDetailModal'
import CameraTile from '../components/CameraTile'
import OperationLog from '../components/OperationLog'
import ViolationList from '../components/violations/ViolationList'
import SectionHeader from '../components/SectionHeader'
import { confirmAction } from '../utils/confirm'

export default function LiveMonitor() {
  const settings = useStore((s) => s.settings)
  const { cameras, zaloToken, zaloTargetId } = settings
  const addViolation = useStore((s) => s.addViolation)
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

  // Khi khởi động trang, cố gắng tải danh sách camera và vùng vẽ từ backend nếu có
  useEffect(() => {
    (async () => {
      try {
        const list = await streams.listCameras()
        // Thay vì merge, đồng bộ tuyệt đối theo server để tránh rác khi đã xóa DB
        const cams = (list || []).map((c) => ({ id: c.id, name: c.name, rtsp: c.rtsp, location: c.location }))
        const regionsMap: any = {}
        for (const cam of list || []) {
          if (cam.regions) regionsMap[cam.id] = cam.regions
        }
        updateSettings({ cameras: cams, cameraRegions: regionsMap })
      } catch {}
    })()
  }, [updateSettings])

  // Fetch violations từ backend
  useEffect(() => {
    const fetchViolations = async () => {
      try {
        const response = await getViolations({ limit: 100, status: 'detected' })
        
        const violationsFromAPI: Violation[] = response.data.map((v) => ({
          id: v.id,
          time: v.timestamp,
          cameraId: v.camera_id,
          cameraName: v.camera_name || `Camera ${v.camera_id}`,
          location: v.location || 'Không rõ',
          vehicleType: v.vehicle_type,
          plate: v.license_plate,
          confidence: v.confidence,
          type: 'Phát hiện',
          status: 'Mới',
          images: {
            overview: v.images.full_frame || '',
            vehicle: v.images.vehicle_crop || '',
            plate: v.images.plate_crop || '',
          },
        }))
        
        for (const violation of violationsFromAPI) {
          addViolation(violation)
        }
      } catch (e) {
        console.error('Lỗi fetch violations:', e)
      }
    }
    
    fetchViolations()
    const interval = setInterval(fetchViolations, 5000)
    return () => clearInterval(interval)
  }, [addViolation])

  // Poll vehicle density từ backend mỗi 2 giây
  useEffect(() => {
    if (!cameras || cameras.length === 0) return
    
    const fetchDensities = async () => {
      const densities: Record<string, number> = {}
      for (const cam of cameras) {
        try {
          const info = await streams.getCameraDensity(cam.rtsp)
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
  const pendingList = useMemo(() => violations.filter(v => v.status === 'Mới').slice(0, 50), [violations])
  const filtered = useMemo(() => (filter === 'Tất cả' ? pendingList : pendingList.filter(v => v.type === filter)), [pendingList, filter])
  const screens = Grid.useBreakpoint()
  const isMobile = !screens.md

  const counts = useMemo(() => {
    const pending = violations.filter(v => v.status === 'Mới')
    const total = pending.length
    const red = pending.filter(v => v.type === 'Vượt đèn đỏ').length
    const speed = pending.filter(v => v.type === 'Quá tốc độ').length
    const helmet = pending.filter(v => v.type === 'Không đội mũ').length
    return { total, red, speed, helmet }
  }, [violations])

  async function onConfirm(v: Violation): Promise<boolean> {
    const ok = await confirmAction('Xác nhận vi phạm này?')
    if (!ok) return false
    await confirmViolation(v.id)
    updateViolation(v.id, { status: 'Đã xác nhận' })
    toast.success('Đã xác nhận vi phạm')
    useStore.getState().addOperationLog({
      id: `${v.id}-confirm-${Date.now()}`,
      timestamp: new Date().toISOString(),
      user: '',
      action: 'confirm',
      violationType: v.type,
      plate: v.plate,
      camera: v.cameraName,
      details: 'Xác nhận vi phạm'
    })
    if (zaloToken && zaloTargetId) {
      await sendZalo(v, zaloToken, zaloTargetId)
    }
    return true
  }

  async function onSkip(v: Violation): Promise<boolean> {
    const ok = await confirmAction('Bỏ qua vi phạm này?')
    if (!ok) return false
    await skipViolation(v.id)
    updateViolation(v.id, { status: 'Đã bỏ qua' })
    toast('Đã bỏ qua', { icon: '🗑️' })
    useStore.getState().addOperationLog({
      id: `${v.id}-skip-${Date.now()}`,
      timestamp: new Date().toISOString(),
      user: '',
      action: 'skip',
      violationType: v.type,
      plate: v.plate,
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
            <OperationLog onSelect={({ plate, violationType, camera }) => {
              // Tìm vi phạm phù hợp nhất để mở modal chi tiết
              let candidate: Violation | undefined = undefined
              if (plate) {
                candidate = pendingList.find(v => v.plate === plate)
              }
              if (!candidate && violationType) {
                // Ưu tiên khớp theo loại + camera
                candidate = pendingList.find(v => v.type === violationType && (!camera || v.cameraName === camera))
              }
              if (!candidate && violationType) {
                // Fallback: bất kỳ vi phạm cùng loại gần nhất
                candidate = pendingList.find(v => v.type === violationType)
              }
              if (!candidate) {
                // Fallback cuối: phần tử gần nhất
                candidate = pendingList[0]
              }
              setSelected(candidate ?? null)
              // Đặt cờ read-only khi mở từ nhật ký
              setModalReadOnly(true)
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
        onConfirm={async () => (selected ? await onConfirm(selected) : false)}
        onSkip={async () => (selected ? await onSkip(selected) : false)}
        readOnly={modalReadOnly}
      />
    </Row>
  )
}
