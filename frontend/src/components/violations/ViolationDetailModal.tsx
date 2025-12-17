import { Modal, Row, Col, Tag, Button, Typography, Select, Input } from 'antd'
import toast from 'react-hot-toast'
import { useEffect, useState } from 'react'
import type { Violation, ViolationType } from '../../store/useStore'
import { isPlaceholder } from '../../utils/media'
import { STATUS_TAG_COLOR, violationTypeToTagColor, getViolationTypes } from '../../constants/violations'
import type { ViolationStatus } from '../../store/useStore'
import { updateViolation } from '../../services/violations'

const { Text } = Typography
const { Option } = Select

interface ConfirmPayload {
  types?: ViolationType[]
  vehicleType?: string | null
  plate?: string | null
}

export default function ViolationDetailModal({ open, onClose, data, onConfirm, onSkip, readOnly = false }: { open: boolean; onClose: () => void; data?: Violation; onConfirm?: (payload?: ConfirmPayload) => Promise<boolean>; onSkip?: (payload?: ConfirmPayload) => Promise<boolean>; readOnly?: boolean }) {
  const violationLabels = data ? getViolationTypes(data) : []
  const rawCameraName = (data?.cameraName ?? '').trim()
  const normalizedCamera = rawCameraName ? rawCameraName.toLowerCase() : ''
  const tagMatchesCamera = rawCameraName
    ? violationLabels.some((label) => label.toLowerCase() === normalizedCamera)
    : false
  const cameraLabel = tagMatchesCamera
    ? (data?.cameraId ? `Camera ${data.cameraId}` : '')
    : (rawCameraName || (data?.cameraId ? `Camera ${data.cameraId}` : ''))
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewSrc, setPreviewSrc] = useState<string | null>(null)
  const [acting, setActing] = useState<'confirm' | 'skip' | null>(null)
  const [finalStatus, setFinalStatus] = useState<string | null>(null)

  // State cho các field có thể chỉnh sửa
  const [editableTypes, setEditableTypes] = useState<ViolationType[]>([])
  const [editableVehicleType, setEditableVehicleType] = useState<string>('')
  const [editablePlate, setEditablePlate] = useState<string>('')

  // Reset trạng thái khi mở modal mới hoặc chuyển sang vi phạm khác
  useEffect(() => {
    if (open && data) {
      setActing(null)
      setFinalStatus(null)
      setEditableVehicleType(data.vehicleType || '')
      setEditablePlate(data.plate || '')
    }
  }, [open, data?.id])

  useEffect(() => {
    if (open && data) {
      const nextTypes = violationLabels.length ? violationLabels : [data.type]
      // Tự động gỡ 'Phát hiện' nếu có vi phạm khác
      const filtered = nextTypes.filter((t, idx, arr) => {
        if (t === 'Phát hiện') {
          const hasOther = arr.some(x => x !== 'Phát hiện')
          return !hasOther
        }
        return true
      })
      setEditableTypes((filtered.length > 0 ? filtered : ['Phát hiện']) as ViolationType[])
    }
  }, [open, data, violationLabels.join('|')])

  function openPreview(src?: string) {
    if (!src || isPlaceholder(src)) {
      setPreviewSrc(null)
      setPreviewOpen(true)
    } else {
      setPreviewSrc(src)
      setPreviewOpen(true)
    }
  }
  const status = finalStatus ?? data?.status ?? 'Mới'
  const isPending = status === 'Mới'

  const handleConfirm = async () => {
    if (!isPending || readOnly || acting || !data?.trackId) return
    try {
      setActing('confirm')

      // Gửi dữ liệu đã chỉnh sửa lên backend trước khi confirm
      const updateData: {
        violation_tags?: string[]  // Chỉ dùng violation_tags
        vehicle_type?: string
        license_plate?: string
      } = {}
      const payload: ConfirmPayload = {}

      // Map frontend type về backend violation_tags
      if (JSON.stringify(editableTypes) !== JSON.stringify(violationLabels)) {
        const mapLabel = (label: string): string => {
          const typeMap: Record<string, string> = {
            'Phát hiện': 'detected',
            'Vượt đèn đỏ': 'red_light',
            'Không đội mũ': 'no_helmet',
            'Quá tốc độ': 'speed_violation',
          }
          return typeMap[label] || 'detected'
        }
        const backendTypes = editableTypes.map(mapLabel)
        if (backendTypes.length > 0) {
          updateData.violation_tags = backendTypes
          payload.types = [...editableTypes]
        }
      } else if (violationLabels.length) {
        payload.types = [...violationLabels] as ViolationType[]
      } else {
        payload.types = data ? [data.type] : undefined
      }
      if (editableVehicleType !== (data.vehicleType || '')) {
        updateData.vehicle_type = editableVehicleType || undefined
        payload.vehicleType = editableVehicleType || null
      }
      if (editablePlate !== (data.plate || '')) {
        updateData.license_plate = editablePlate || undefined
        payload.plate = editablePlate
      }

      // Update violation nếu có thay đổi
      if (Object.keys(updateData).length > 0) {
        try {
          await updateViolation(data.trackId, updateData)
          toast.success('Đã cập nhật thông tin vi phạm')
        } catch (e) {
          console.error('Lỗi update violation:', e)
          toast.error('Lỗi cập nhật thông tin, vẫn tiếp tục xác nhận')
        }
      }

      // Gọi onConfirm để confirm violation
      // Backend sẽ tự động gửi Discord notification
      const ok = await Promise.resolve(onConfirm?.(payload))

      // Chỉ cập nhật cục bộ khi thao tác thành công
      if (ok === true) {
        setFinalStatus('Đã xác nhận')
        toast.success('Đã xác nhận vi phạm')
      }
    } finally {
      setActing(null)
    }
  }

  const handleSkip = async () => {
    if (!isPending || readOnly || acting) return
    try {
      setActing('skip')
      const payload: ConfirmPayload = {
        types: editableTypes.length
          ? [...editableTypes]
          : (violationLabels.length
            ? [...violationLabels] as ViolationType[]
            : (data ? [data.type] : undefined)),
        vehicleType: editableVehicleType !== (data?.vehicleType || '') ? (editableVehicleType || null) : undefined,
        plate: editablePlate !== (data?.plate || '') ? editablePlate : undefined,
      }
      const ok = await Promise.resolve(onSkip?.(payload))
      // Chỉ cập nhật cục bộ khi thao tác thành công
      if (ok === true) {
        setFinalStatus('Đã bỏ qua')
        toast.success('Đã bỏ qua vi phạm')
      }
    } finally {
      setActing(null)
    }
  }

  return (
    <Modal open={open} onCancel={onClose} width={900} footer={null} title="Chi tiết vi phạm">
      {data && (
        <div className="viol-modal">
          <div className="viol-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {violationLabels.length
                    ? violationLabels.map((label) => (
                      <Tag key={label} color={violationTypeToTagColor(label)}>{label}</Tag>
                    ))
                    : <Tag color={violationTypeToTagColor(data.type)}>{data.type}</Tag>}
                </div>
                {cameraLabel && <Text strong>{cameraLabel}</Text>}
                <Text type="secondary">
                  {cameraLabel ? '• ' : ''}
                  {data.location || '—'}
                </Text>
                {data.vehicleType && <Tag>{data.vehicleType}</Tag>}
                <Tag color={STATUS_TAG_COLOR[status as ViolationStatus]}>{status === 'Mới' ? 'Chờ duyệt' : status}</Tag>
              </div>
          </div>

          <Row gutter={16}>
            <Col xs={24} md={13}>
              {/* Ảnh toàn cảnh mặc định, không cần Segmented */}
              <div className="img-tile zoomable" style={{ height: 280 }} onDoubleClick={() => openPreview(data.images?.overview)}>
                {isPlaceholder(data.images?.overview) ? (
                  <div className="img-blank" />
                ) : (
                  <img src={data.images.overview} alt="overview" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 12 }} />
                )}
              </div>

              {/* 2 ảnh nhỏ bên dưới */}
              <Row gutter={12} style={{ marginTop: 12 }}>
                <Col span={12}>
                  <div className="img-tile zoomable" style={{ height: 120 }} onDoubleClick={() => openPreview(data.images?.vehicle)}>
                    {isPlaceholder(data.images?.vehicle) ? (
                      <div className="img-blank" />
                    ) : (
                      <img src={data.images.vehicle} alt="vehicle" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 12 }} />
                    )}
                  </div>
                  <div className="section-title">Ảnh phương tiện</div>
                </Col>
                <Col span={12}>
                  <div className="img-tile zoomable" style={{ height: 120 }} onDoubleClick={() => openPreview(data.images?.plate)}>
                    {isPlaceholder(data.images?.plate) ? (
                      <div className="img-blank" />
                    ) : (
                      <img src={data.images.plate} alt="plate" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 12 }} />
                    )}
                  </div>
                  <div className="section-title">Ảnh biển số</div>
                </Col>
              </Row>
            </Col>

            <Col xs={24} md={11}>
              {/* Thông tin được nhóm thành các card đẹp hơn */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {/* Card thông tin chính */}
                <div className="info-card">
                  <div className="info-card-title">Thông tin vi phạm</div>
                  <div className="info-row">
                    <span className="info-label">Loại vi phạm</span>
                    {isPending && !readOnly ? (
                      <Select
                        mode="multiple"
                        value={editableTypes}
                        onChange={(vals) => {
                          // Tự động gỡ 'Phát hiện' nếu chọn vi phạm khác
                          let filtered = vals
                          const hasOther = filtered.some(x => x !== 'Phát hiện')
                          if (hasOther) {
                            filtered = filtered.filter(x => x !== 'Phát hiện')
                          }
                          setEditableTypes((filtered.length ? filtered : ['Phát hiện']) as ViolationType[])
                        }}
                        style={{ minWidth: 220, marginLeft: 'auto' }}
                        size="small"
                        tagRender={({ label }) => (
                          <Tag style={{ margin: 0 }} color={violationTypeToTagColor(String(label))}>
                            {label}
                          </Tag>
                        )}
                      >
                        <Option value="Phát hiện">Phát hiện</Option>
                        <Option value="Vượt đèn đỏ">Vượt đèn đỏ</Option>
                        <Option value="Không đội mũ">Không đội mũ</Option>
                        <Option value="Quá tốc độ">Quá tốc độ</Option>
                      </Select>
                    ) : (
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginLeft: 'auto' }}>
                        {(violationLabels.length ? violationLabels : [data.type]).map((label) => (
                          <Tag key={label} color={violationTypeToTagColor(label)}>{label}</Tag>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="info-row">
                    <span className="info-label">Phương tiện</span>
                    {isPending && !readOnly ? (
                      <Select
                        value={editableVehicleType}
                        onChange={setEditableVehicleType}
                        style={{ width: 150, marginLeft: 'auto' }}
                        size="small"
                        allowClear
                      >
                        <Option value="car">Car</Option>
                        <Option value="motorcycle">Motorcycle</Option>
                        <Option value="bus">Bus</Option>
                        <Option value="truck">Truck</Option>
                      </Select>
                    ) : (
                      <span className="info-value">{data.vehicleType ?? '—'}</span>
                    )}
                  </div>
                  <div className="info-row">
                    <span className="info-label">Biển số</span>
                    {isPending && !readOnly ? (
                      <Input
                        value={editablePlate}
                        onChange={(e) => setEditablePlate(e.target.value)}
                        style={{ width: 150, marginLeft: 'auto' }}
                        size="small"
                        placeholder="Nhập biển số"
                      />
                    ) : (
                      <span className="info-value">{data.plate ?? '—'}</span>
                    )}
                  </div>
                  <div className="info-row">
                    <span className="info-label">Tốc độ</span>
                    <span className="info-value">{typeof data.speed === 'number' ? `${data.speed.toFixed(1)} km/h` : '—'}</span>
                  </div>
                  {data.trackId && (
                    <div className="info-row">
                      <span className="info-label">Track ID</span>
                      <span className="info-value" style={{ fontFamily: 'monospace' }}>{data.trackId}</span>
                    </div>
                  )}
                </div>

                {/* Card thông tin hệ thống */}
                <div className="info-card">
                  <div className="info-card-title">Thông tin hệ thống</div>
                  <div className="info-row">
                    <span className="info-label">Thời gian</span>
                    <span className="info-value">{new Date(data.time).toLocaleString('vi-VN')}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Camera</span>
                    <span className="info-value">{data.cameraName}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Vị trí địa điểm</span>
                    <span className="info-value">{data.location || '—'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Trạng thái</span>
                    <Tag color={STATUS_TAG_COLOR[status as ViolationStatus]} style={{ marginLeft: 'auto' }}>
                      {status === 'Mới' ? 'Chờ duyệt' : status}
                    </Tag>
                  </div>
                </div>
              </div>
            </Col>
          </Row>

          {/* 2 nút hành động ở giữa modal */}
          {!readOnly && (
            <div style={{ marginTop: 20, display: 'flex', gap: 16, justifyContent: 'center' }}>
              <Button onClick={handleConfirm} type="primary" size="large" style={{ minWidth: 140 }} disabled={!isPending || acting === 'confirm'} loading={acting === 'confirm'}>
                Xác nhận
              </Button>
              <Button onClick={handleSkip} danger size="large" style={{ minWidth: 140 }} disabled={!isPending || acting === 'skip'} loading={acting === 'skip'}>
                Bỏ qua
              </Button>
            </div>
          )}

          {/* Preview toàn màn hình hơn, hỗ trợ double click để đóng */}
          <Modal
            open={previewOpen}
            onCancel={() => setPreviewOpen(false)}
            footer={null}
            width="auto"
            centered
            className="preview-modal"
            styles={{
              body: { padding: 0, background: 'transparent' },
              content: { padding: 0, background: 'transparent', border: 'none' }
            }}
          >
            {previewSrc ? (
              <img
                className={previewSrc === data?.images?.overview ? "preview-img-overview" : "preview-img"}
                src={previewSrc}
                alt="preview"
                onDoubleClick={() => setPreviewOpen(false)}
              />
            ) : (
              <div className="preview-blank" onDoubleClick={() => setPreviewOpen(false)} />
            )}
          </Modal>
        </div>
      )}
    </Modal>
  )
}
