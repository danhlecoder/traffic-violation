import { Modal, Row, Col, Tag, Button, Typography } from 'antd'
import toast from 'react-hot-toast'
import { useEffect, useState } from 'react'
import type { Violation } from '../../store/useStore'
import { isPlaceholder } from '../../utils/media'
import { STATUS_TAG_COLOR, violationTypeToTagColor } from '../../constants/violations'
import type { ViolationStatus } from '../../store/useStore'

const { Text } = Typography

export default function ViolationDetailModal({ open, onClose, data, onConfirm, onSkip, readOnly = false }: { open: boolean; onClose: () => void; data?: Violation; onConfirm?: () => Promise<boolean>; onSkip?: () => Promise<boolean>; readOnly?: boolean }) {
  const t = data ? { tag: violationTypeToTagColor(data.type) } : undefined
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewSrc, setPreviewSrc] = useState<string | null>(null)
  const [acting, setActing] = useState<'confirm' | 'skip' | null>(null)
  const [finalStatus, setFinalStatus] = useState<string | null>(null)
  const [videoOpen, setVideoOpen] = useState(false)

  // Reset trạng thái khi mở modal mới hoặc chuyển sang vi phạm khác
  useEffect(() => {
    if (open) {
      setActing(null)
      setFinalStatus(null)
    }
  }, [open, data?.id])

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
  const videoUrl: string | undefined = (data as any)?.videoUrl || (data as any)?.video

  const handleConfirm = async () => {
    if (!isPending || readOnly || acting) return
    try {
      setActing('confirm')
      const ok = await Promise.resolve(onConfirm?.())
      // Chỉ cập nhật cục bộ khi thao tác thành công
      if (ok === true) setFinalStatus('Đã xác nhận')
    } finally {
      setActing(null)
    }
  }

  const handleSkip = async () => {
    if (!isPending || readOnly || acting) return
    try {
      setActing('skip')
      const ok = await Promise.resolve(onSkip?.())
      // Chỉ cập nhật cục bộ khi thao tác thành công
      if (ok === true) setFinalStatus('Đã bỏ qua')
    } finally {
      setActing(null)
    }
  }

  return (
    <Modal open={open} onCancel={onClose} width={900} footer={null} title="Chi tiết vi phạm">
      {data && (
        <div className="viol-modal">
          <div className="viol-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <Tag color={t?.tag}>{data.type}</Tag>
                <Text strong>{data.cameraName}</Text>
                <Text type="secondary">• {data.location || '—'}</Text>
                {data.vehicleType && <Tag>{data.vehicleType}</Tag>}
                <Tag color={STATUS_TAG_COLOR[status as ViolationStatus]}>{status === 'Mới' ? 'Chờ duyệt' : status}</Tag>
              </div>
              <div>
                <Button size="small" onClick={() => { if (videoUrl) { setVideoOpen(true) } else { toast('Chưa có video minh chứng', { icon: 'ℹ️' }) } }}>Xem video</Button>
              </div>
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
                    <Tag color={t?.tag} style={{ marginLeft: 'auto' }}>{data.type}</Tag>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Phương tiện</span>
                    <span className="info-value">{data.vehicleType ?? '—'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Biển số</span>
                    <span className="info-value">{data.plate ?? '—'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Tốc độ</span>
                    <span className="info-value">{typeof data.speed === 'number' ? `${data.speed} km/h` : '—'}</span>
                  </div>
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
          <Modal open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={1000} centered>
            <div onDoubleClick={() => setPreviewOpen(false)}>
              {previewSrc ? (
                <img className="preview-img" src={previewSrc} alt="preview" />
              ) : (
                <div className="preview-blank" />
              )}
            </div>
          </Modal>
          {videoUrl && (
            <Modal open={videoOpen} onCancel={() => setVideoOpen(false)} footer={null} width={900} title="Video minh chứng">
              <video src={videoUrl} controls style={{ width: '100%', borderRadius: 8 }} />
            </Modal>
          )}
        </div>
      )}
    </Modal>
  )
}
