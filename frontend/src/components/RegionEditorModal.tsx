import { Modal, Button, Space, Tooltip, Typography, message } from 'antd'
import { useCallback, useEffect, useRef, useState } from 'react'
import { LineOutlined, HighlightOutlined, ClearOutlined, CheckOutlined, CloseOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { useStore } from '../store/useStore'
import RegionOverlay from './RegionOverlay'
import { useElementScaler } from '../hooks/useElementScaler'
import { useRegionDrawing } from '../hooks/useRegionDrawing'
import { streams } from '../services/api'
import * as streamSvc from '../services/streams'

const { Text } = Typography

type Mode = 'idle' | 'draw-line' | 'draw-roi'

export default function RegionEditorModal({
  open,
  cameraId,
  imageSrc,
  rtsp,
  onClose,
}: {
  open: boolean
  cameraId: string
  imageSrc?: string
  rtsp?: string
  onClose: () => void
}) {
  const regions = useStore((s) => s.settings.cameraRegions)
  const setCameraRegion = useStore((s) => s.setCameraRegion)
  const clearCameraRegion = useStore((s) => s.clearCameraRegion)
  const cameraRegion = regions[cameraId] || {}

  const { ref: containerRef, toRelative, toPixel } = useElementScaler<HTMLDivElement>()
  const { mode, setMode, tempLine, tempRoi, clickAddPoint, commitLine, commitRoi, cancel } = useRegionDrawing(
    async (p1, p2) => {
      // Lưu vào store và gọi API backend (merge không xóa roi)
      const payload = { stopLine: [p1, p2] as any }
      setCameraRegion(cameraId, payload)
      await streams.updateCameraRegions(cameraId, payload)
    },
    async (pts) => {
      // Lưu ROI nhưng giữ nguyên stopLine hiện có (backend merge từng phần)
      const payload = { roi: pts as any }
      setCameraRegion(cameraId, payload)
      await streams.updateCameraRegions(cameraId, payload)
    }
  )

  const [loadingDetect, setLoadingDetect] = useState(false)
  const [loadingRegions, setLoadingRegions] = useState(false)

  // Tạo ROI tự động từ lineB hiện tại
  const createAutoROI = useCallback(async () => {
    const lineB = cameraRegion.lineB
    if (!lineB || lineB.length !== 2) {
      message.error('Cần có lineB trước. Click "Line tự động" để tạo.')
      return
    }

    try {
      // Tính y trung bình của lineB làm cạnh trên
      const y_top = (lineB[0].y + lineB[1].y) / 2

      // Tạo 4 điểm ROI: từ lineB xuống đáy, kéo dài hết chiều ngang
      const roi = [
        { x: 0, y: y_top },   // Top-left
        { x: 1, y: y_top },   // Top-right
        { x: 1, y: 1 },       // Bottom-right
        { x: 0, y: 1 },       // Bottom-left
      ]

      setCameraRegion(cameraId, { roi })
      await streams.updateCameraRegions(cameraId, { roi })
      message.success('Đã tạo ROI tự động từ lineB')
    } catch (e: any) {
      message.error(`Lỗi tạo ROI: ${e?.message || e}`)
    }
  }, [cameraRegion.lineB, cameraId, setCameraRegion])

  // Khi modal mở, nạp ngay regions từ backend để tránh lệ thuộc store cũ
  useEffect(() => {
    if (!open || !cameraId) return
    let aborted = false
    ;(async () => {
      setLoadingRegions(true)
      try {
        const cam = await streamSvc.getCamera(cameraId)
        if (!aborted && cam?.regions) {
          setCameraRegion(cameraId, cam.regions as any)
        }
      } catch {}
      finally {
        if (!aborted) setLoadingRegions(false)
      }
    })()
    return () => { aborted = true }
  }, [open, cameraId, setCameraRegion])

  const runAutoDetect = useCallback(async () => {
    if (!rtsp) {
      message.warning('Chưa cấu hình RTSP cho camera này')
      return
    }
    if (!imageSrc) {
      message.warning('Chưa có ảnh snapshot để phát hiện. Hãy chờ ảnh xuất hiện hoặc thử chụp lại.')
      return
    }
    setLoadingDetect(true)
    try {
      // Ưu tiên dùng ngay ảnh đang hiển thị (nếu có) để detect
      let resp: Response | undefined
      let dataUrl: string | null = null
      if (imageSrc) {
        if (imageSrc.startsWith('data:image/')) {
          dataUrl = imageSrc
        } else if (imageSrc.startsWith('blob:')) {
          try {
            const blob = await fetch(imageSrc).then(r => r.blob())
            dataUrl = await new Promise<string>((resolve, reject) => {
              const reader = new FileReader()
              reader.onloadend = () => resolve(reader.result as string)
              reader.onerror = reject
              reader.readAsDataURL(blob)
            })
          } catch {}
        }
      }

      // Dùng CHÍNH ảnh đang hiển thị: chuyển blob -> data URL nếu cần và POST lên /api/detect/stopline
      let dataUrlLocal: string | null = null
      if (imageSrc) {
        if (imageSrc.startsWith('data:image/')) {
          dataUrlLocal = imageSrc
        } else if (imageSrc.startsWith('blob:')) {
          try {
            const blob = await fetch(imageSrc).then(r => r.blob())
            dataUrlLocal = await new Promise<string>((resolve, reject) => {
              const reader = new FileReader()
              reader.onloadend = () => resolve(reader.result as string)
              reader.onerror = reject
              reader.readAsDataURL(blob)
            })
          } catch {}
        }
      }

      if (!dataUrlLocal) throw new Error('Không có ảnh để detect')

      resp = await fetch(`${streamSvc.getApiBase()}/api/detect/stopline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: dataUrlLocal }),
      })
      if (!resp) throw new Error('no response')
      if (!resp.ok) throw new Error(`detect failed: ${resp.status}`)
      const data = await resp.json()
      console.log('🎯 Response data:', data)
      const line = data?.stopLine
      const lineB = data?.lineB
      const roi = data?.roi
      console.log('📍 lineB:', lineB, 'roi:', roi)
      if (line && line.length === 2) {
        const payload: any = { stopLine: line }
        if (lineB && lineB.length === 2) {
          payload.lineB = lineB
        }
        if (roi && roi.length >= 3) {
          payload.roi = roi
        }
        console.log('📦 Payload sẽ gửi:', payload)
        setCameraRegion(cameraId, payload)
        await streams.updateCameraRegions(cameraId, payload)
        const parts = ['stopLine']
        if (lineB) parts.push('lineB')
        if (roi) parts.push('ROI')
        message.success(`Đã phát hiện và lưu: ${parts.join(' + ')}`)
        if (data?.image) {
          // Cập nhật luôn ảnh nếu server trả về
          try { setTimeout(() => setLoadingDetect(false), 0) } catch {}
        }
      } else {
        message.info('Không phát hiện được vạch dừng')
      }
    } catch (e: any) {
      message.error(`Lỗi phát hiện: ${e?.message || e}`)
    } finally {
      setLoadingDetect(false)
    }
  }, [rtsp, cameraId, setCameraRegion, imageSrc])

  const onOverlayClick = useCallback((e: React.MouseEvent) => {
    if (mode === 'idle') return
    const rel = toRelative(e.clientX, e.clientY)
    clickAddPoint(rel)
  }, [mode, toRelative, clickAddPoint])

  // Keyboard shortcuts handled inside useRegionDrawing hook

  return (
    <Modal
      title={`Thiết lập vùng — Camera ${cameraId}`}
      open={open}
      onCancel={onClose}
      footer={null}
      width={980}
      centered
      destroyOnClose
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <InfoCircleOutlined style={{ color: 'var(--muted)' }} />
          <Text type="secondary" style={{ fontSize: 12 }}>
            Nhấp để đặt điểm: Line (2 điểm), ROI (≥3 điểm). Enter để lưu, Esc hủy, Backspace để xóa điểm cuối.
          </Text>
        </div>

        <div style={{ position: 'relative', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)' }}>
          <div ref={containerRef} style={{ position: 'relative', width: '100%', aspectRatio: '16/9' }}>
            {imageSrc ? (
              <img src={imageSrc} alt="snapshot" style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block', userSelect: 'none' }} />
            ) : (
              <div className="camera-stream-inner" style={{ aspectRatio: '16/9' }}>
                <div className="camera-stream-text">Không có ảnh snapshot</div>
              </div>
            )}

            <div onClick={onOverlayClick} className="region-overlay" style={{ cursor: mode === 'idle' ? 'default' : 'crosshair' }} />
            <RegionOverlay region={cameraRegion} toPixel={toPixel} tempLine={tempLine} tempRoi={tempRoi} readOnly />

            {/* Toolbar */}
            <div className="region-toolbar">
              {mode === 'idle' ? (
                <Space size={6}>
                  <Tooltip title="Vẽ vạch dừng (2 điểm)">
                    <Button size="small" icon={<LineOutlined />} onClick={() => setMode('draw-line')}>Line</Button>
                  </Tooltip>
                  <Tooltip title="Vẽ vùng đèn giao thông (đa giác)">
                    <Button size="small" icon={<HighlightOutlined />} onClick={() => setMode('draw-roi')}>ROI</Button>
                  </Tooltip>
                  <Tooltip title="Phát hiện vạch dừng tự động (stopLine + lineB + ROI)">
                    <Button size="small" loading={loadingDetect} disabled={!imageSrc} onClick={runAutoDetect}>Line tự động</Button>
                  </Tooltip>
                  {cameraRegion.lineB && (
                    <Tooltip title="Tạo ROI từ lineB hiện tại">
                      <Button size="small" onClick={createAutoROI}>ROI tự động</Button>
                    </Tooltip>
                  )}
                  {cameraRegion.stopLine && (
                    <Tooltip title="Xóa vạch dừng (và lineB, ROI)">
                      <Button
                        size="small"
                        danger
                        icon={<ClearOutlined />}
                        onClick={async () => {
                          clearCameraRegion(cameraId, 'stopLine')
                          clearCameraRegion(cameraId, 'lineB')
                          clearCameraRegion(cameraId, 'roi')
                          try { await streams.updateCameraRegions(cameraId, { stopLine: null, lineB: null, roi: null }) } catch {}
                        }}
                      >Xóa line</Button>
                    </Tooltip>
                  )}
                  {cameraRegion.roi && (
                    <Tooltip title="Xóa ROI">
                      <Button
                        size="small"
                        danger
                        icon={<ClearOutlined />}
                        onClick={async () => {
                          clearCameraRegion(cameraId, 'roi')
                          try { await streams.updateCameraRegions(cameraId, { roi: null }) } catch {}
                        }}
                      >Xóa ROI</Button>
                    </Tooltip>
                  )}
                </Space>
              ) : (
                <Space size={6}>
                  <Button size="small" icon={<CloseOutlined />} onClick={cancel}>Hủy</Button>
                  {mode === 'draw-line' ? (
                    <Button type="primary" size="small" icon={<CheckOutlined />} disabled={!tempLine.p1 || !tempLine.p2} onClick={commitLine}>Lưu line</Button>
                  ) : (
                    <Button type="primary" size="small" icon={<CheckOutlined />} disabled={tempRoi.length < 3} onClick={commitRoi}>Lưu ROI</Button>
                  )}
                </Space>
              )}
            </div>
          </div>
        </div>
      </div>
    </Modal>
  )
}


