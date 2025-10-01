import { Modal, Button, Space, Tooltip, Typography } from 'antd'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { LineOutlined, HighlightOutlined, ClearOutlined, CheckOutlined, CloseOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { useStore } from '../store/useStore'
import RegionOverlay from './RegionOverlay'
import type { Point } from '../types/regions'

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

  const [mode, setMode] = useState<Mode>('idle')
  const [tempLine, setTempLine] = useState<{ p1?: Point; p2?: Point }>({})
  const [tempRoi, setTempRoi] = useState<Array<Point>>([])
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open) {
      setMode('idle')
      setTempLine({})
      setTempRoi([])
    }
  }, [open])

  const toRelative = useCallback((clientX: number, clientY: number) => {
    const el = containerRef.current
    if (!el) return { x: 0, y: 0 }
    const rect = el.getBoundingClientRect()
    const x = (clientX - rect.left) / rect.width
    const y = (clientY - rect.top) / rect.height
    return { x: Math.max(0, Math.min(1, x)), y: Math.max(0, Math.min(1, y)) }
  }, [])

  const toPixel = useCallback((pt: { x: number; y: number }) => {
    const el = containerRef.current
    if (!el) return { x: 0, y: 0 }
    const rect = el.getBoundingClientRect()
    return { x: pt.x * rect.width, y: pt.y * rect.height }
  }, [])

  const onOverlayClick = useCallback((e: React.MouseEvent) => {
    if (mode === 'idle') return
    const rel = toRelative(e.clientX, e.clientY)
    if (mode === 'draw-line') {
      if (!tempLine.p1) setTempLine({ p1: rel })
      else if (!tempLine.p2) setTempLine({ p1: tempLine.p1, p2: rel })
      else setTempLine({ p1: rel })
    } else if (mode === 'draw-roi') {
      setTempRoi((prev) => [...prev, rel])
    }
  }, [mode, tempLine, toRelative])

  const commitLine = useCallback(() => {
    if (tempLine.p1 && tempLine.p2) {
      setCameraRegion(cameraId, { stopLine: [tempLine.p1, tempLine.p2] })
      setMode('idle')
      setTempLine({})
    }
  }, [cameraId, setCameraRegion, tempLine])

  const commitRoi = useCallback(() => {
    if (tempRoi.length >= 3) {
      setCameraRegion(cameraId, { roi: tempRoi })
      setMode('idle')
      setTempRoi([])
    }
  }, [cameraId, setCameraRegion, tempRoi])

  const cancelDrawing = useCallback(() => {
    setMode('idle')
    setTempLine({})
    setTempRoi([])
  }, [])

  // Keyboard shortcuts within modal
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (mode === 'draw-roi') {
        if (e.key === 'Escape') cancelDrawing()
        if (e.key === 'Enter') { e.preventDefault(); commitRoi() }
        if (e.key === 'Backspace') setTempRoi((prev) => prev.slice(0, -1))
      } else if (mode === 'draw-line') {
        if (e.key === 'Escape') cancelDrawing()
        if (e.key === 'Enter') commitLine()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, mode, commitLine, commitRoi, cancelDrawing])

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
          <div ref={containerRef} style={{ position: 'relative', width: '100%', height: 'auto' }}>
            {imageSrc ? (
              <img src={imageSrc} alt="snapshot" style={{ width: '100%', height: 'auto', display: 'block', userSelect: 'none' }} />
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
                      <Button size="small" danger icon={<ClearOutlined />} onClick={() => clearCameraRegion(cameraId, 'stopLine')}>Xóa line</Button>
                    </Tooltip>
                  )}
                  {cameraRegion.roi && (
                    <Tooltip title="Xóa ROI">
                      <Button size="small" danger icon={<ClearOutlined />} onClick={() => clearCameraRegion(cameraId, 'roi')}>Xóa ROI</Button>
                    </Tooltip>
                  )}
                </Space>
              ) : (
                <Space size={6}>
                  <Button size="small" icon={<CloseOutlined />} onClick={cancelDrawing}>Hủy</Button>
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


