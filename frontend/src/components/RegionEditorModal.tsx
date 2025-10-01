import { Modal, Button, Space, Tooltip, Typography } from 'antd'
import { useCallback, useRef } from 'react'
import { LineOutlined, HighlightOutlined, ClearOutlined, CheckOutlined, CloseOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { useStore } from '../store/useStore'
import RegionOverlay from './RegionOverlay'
import { useElementScaler } from '../hooks/useElementScaler'
import { useRegionDrawing } from '../hooks/useRegionDrawing'
import { streams } from '../services/api'

const { Text } = Typography

type Mode = 'idle' | 'draw-line' | 'draw-roi'

export default function RegionEditorModal({
  open,
  cameraId,
  imageSrc,
  onClose,
}: {
  open: boolean
  cameraId: string
  imageSrc?: string
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
                  {cameraRegion.stopLine && (
                    <Tooltip title="Xóa vạch dừng">
                      <Button
                        size="small"
                        danger
                        icon={<ClearOutlined />}
                        onClick={async () => {
                          clearCameraRegion(cameraId, 'stopLine')
                          try { await streams.updateCameraRegions(cameraId, { stopLine: null }) } catch {}
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


