import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { Row, Col, Space, Select, Button, Grid, Card, Pagination } from 'antd'
import { useStore, VIOLATION_TYPES, Violation } from '../store/useStore'
import { confirmViolation, sendZalo, skipViolation } from '../services/api'
import ViolationDetailModal from '../components/ViolationDetailModal'
import CameraTile from '../components/CameraTile'
import OperationLog from '../components/OperationLog'
import ViolationList from '../components/ViolationList'
import SectionHeader from '../components/SectionHeader'
import { confirmAction } from '../utils/confirm'

function randomPlate() {
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const nums = () => Math.floor(Math.random() * 10)
  return `${Math.floor(Math.random() * 99)}${letters[Math.floor(Math.random() * letters.length)]}-${nums()}${nums()}${nums()}${nums()}${nums()}`
}

function createMockViolation(cam: { id: string; name: string; location: string }, settings: ReturnType<typeof useStore.getState>['settings']): Violation {
  const type = VIOLATION_TYPES[Math.floor(Math.random() * VIOLATION_TYPES.length)]
  const speed = type === 'Quá tốc độ' ? settings.speedLimit + Math.floor(Math.random() * 50) : undefined
  return {
    id: `V${Date.now()}-${Math.floor(Math.random() * 999)}`,
    type,
    cameraId: cam.id,
    cameraName: cam.name,
    location: cam.location,
    time: new Date().toISOString(),
    speed,
    plate: randomPlate(),
    vehicleType: Math.random() > 0.5 ? 'Xe máy' : 'Ô tô',
    confidence: Math.round((0.6 + Math.random() * 0.39) * 100) / 100,
    images: {
      overview: '/placeholders/panorama.svg',
      vehicle: '/placeholders/vehicle.svg',
      plate: '/placeholders/plate.svg',
    },
    status: 'Mới',
  }
}

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

  // Lưu trạng thái UI khi thay đổi
  useEffect(() => {
    updateSettings({
      monitorShowAll: showAll,
      monitorSelectedCamIds: selectedCamIds,
      monitorFocusedCamId: focusedCamId,
      monitorPage: currentPage,
    })
  }, [showAll, selectedCamIds, focusedCamId, currentPage, updateSettings])

  // Tạo luồng dữ liệu giả lập
  useEffect(() => {
    const interval = setInterval(() => {
      const cam = cameras[Math.floor(Math.random() * cameras.length)]
      const v = createMockViolation(cam, useStore.getState().settings)
      addViolation(v)
    }, 5000)
    return () => clearInterval(interval)
  }, [addViolation, cameras])

  const [filter, setFilter] = useState<'Tất cả' | 'Vượt đèn đỏ' | 'Quá tốc độ' | 'Không đội mũ'>('Tất cả')
  const pendingList = useMemo(() => violations.filter(v => v.status === 'Mới').slice(0, 50), [violations])
  const filtered = useMemo(() => (filter === 'Tất cả' ? pendingList : pendingList.filter(v => v.type === filter)), [pendingList, filter])
  const screens = Grid.useBreakpoint()
  const isMobile = !screens.md

  const counts = useMemo(() => {
    const pending = violations.filter(v => v.status === 'Mới')
    const total = pending.length
    const red = pending.filter(v => v.type === 'Vượt đèn đỏ').length
    const spd = pending.filter(v => v.type === 'Quá tốc độ').length
    const helm = pending.filter(v => v.type === 'Không đội mũ').length
    return { total, red, spd, helm }
  }, [violations])

  async function onConfirm(v: Violation) {
    const ok = await confirmAction('Xác nhận vi phạm này?')
    if (!ok) return
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

    const pages = Math.max(1, Math.ceil(cams.length / CAMERAS_PER_PAGE))
    return { allCams: cams, totalPages: pages }
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
                      name={cam.name}
                      location={cam.location}
                      rtsp={cam.rtsp}
                      vehicleDensity={Math.floor(Math.random() * 25)} // Demo data - thay bằng data thật sau
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
                <span className="tab-count">{counts.spd}</span>
              </div>
              <div
                className={`filter-tab gold ${filter === 'Không đội mũ' ? 'active' : ''}`}
                onClick={() => setFilter('Không đội mũ')}
              >
                <span className="tab-label">Không đội mũ</span>
                <span className="tab-count">{counts.helm}</span>
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
        onConfirm={() => selected && onConfirm(selected)}
        onSkip={() => selected && onSkip(selected)}
        readOnly={modalReadOnly}
      />
    </Row>
  )
}
