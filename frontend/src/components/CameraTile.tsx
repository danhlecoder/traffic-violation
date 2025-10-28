import { Badge, Typography, Tag, Button, Tooltip } from 'antd'
import { useMemo, useState, useCallback, useEffect, useRef } from 'react'
import { EditOutlined } from '@ant-design/icons'
import { buildStreamUrl } from '../services/streams'
import { streams } from '../services/api'
import RegionEditorModal from './RegionEditorModal'
import RegionOverlay from './RegionOverlay'
import { useStore } from '../store/useStore'
import { useElementScaler } from '../hooks/useElementScaler'

const { Text } = Typography

export default function CameraTile({
  cameraId,
  name,
  location,
  rtsp,
  height,
  onDoubleClick,
  focused,
  vehicleDensity = 0 // Mật độ phương tiện mặc định là 0
}: {
  cameraId: string;
  name: string;
  location?: string;
  rtsp?: string;
  height?: number | string;
  onDoubleClick?: () => void;
  focused?: boolean;
  vehicleDensity?: number;
}) {
  const ready = useMemo(() => Boolean(rtsp), [rtsp])
  const { ref: containerRef, toPixel } = useElementScaler<HTMLDivElement>()
  const [editorOpen, setEditorOpen] = useState(false)
  const [snapshot, setSnapshot] = useState<string | undefined>(undefined)
  const autoDetectRanRef = useRef(false)
  const autoDetectingRef = useRef(false)
  const regions = useStore((s) => s.settings.cameraRegions)
  const setCameraRegion = useStore((s) => s.setCameraRegion)
  const cameraRegion = regions[cameraId] || {}

  const streamSrc = useMemo(() => (rtsp ? buildStreamUrl(rtsp) : undefined), [rtsp])

  // Tự động chụp khung đầu và detect khi stream sẵn sàng (chỉ khi chưa có line)
  const tryAutoDetectFromStream = useCallback(async (): Promise<boolean> => {
    if (!rtsp || autoDetectRanRef.current || autoDetectingRef.current) return false
    if (cameraRegion && (cameraRegion as any).stopLine) return false
    const el = containerRef.current
    const img = el?.querySelector('img') as HTMLImageElement | null
    if (!img || !(img.naturalWidth || img.width)) return false
    try {
      autoDetectingRef.current = true
      const canvas = document.createElement('canvas')
      const w = img.naturalWidth || img.width
      const h = img.naturalHeight || img.height
      canvas.width = w
      canvas.height = h
      const ctx = canvas.getContext('2d')
      if (!ctx) throw new Error('No canvas context')
      ctx.drawImage(img, 0, 0, w, h)
      const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
      const apiBase = (import.meta as any)?.env?.VITE_API_BASE || `${window.location.protocol}//${window.location.hostname}:8000`
      const resp = await fetch(`${apiBase}/v1/detection/stopline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: dataUrl }),
      })
      if (!resp.ok) throw new Error('auto detect failed')
      const data = await resp.json()
      const line = data?.stopLine
      const lineB = data?.lineB
      const roi = data?.roi
      if (line && line.length === 2) {
        const payload: any = { stopLine: line }
        if (lineB && lineB.length === 2) {
          payload.lineB = lineB
        }
        if (roi && roi.length >= 3) {
          payload.roi = roi
        }
        setCameraRegion(cameraId, payload)
        try { await streams.updateCameraRegions(cameraId, payload) } catch {}
        autoDetectRanRef.current = true
        return true
      }
    } catch {
      // ignore errors silently
    } finally {
      autoDetectingRef.current = false
    }
    return false
  }, [rtsp, cameraRegion, cameraId, setCameraRegion])

  // Capture a snapshot via backend endpoint; fallback to canvas if needed
  const takeSnapshot = useCallback(async () => {
    if (!rtsp) return
    // Xóa ảnh cũ để tránh hiển thị ảnh trước đó khi mở modal
    setSnapshot(undefined)
    // Ưu tiên chụp trực tiếp từ khung stream đang hiển thị (nhanh, 0ms)
    const el = containerRef.current
    const img = el?.querySelector('img') as HTMLImageElement | null
    if (img && (img.naturalWidth || img.width) > 0) {
      try {
        const canvas = document.createElement('canvas')
        const w = img.naturalWidth || img.width
        const h = img.naturalHeight || img.height
        canvas.width = w
        canvas.height = h
        const ctx = canvas.getContext('2d')
        if (!ctx) throw new Error('No canvas context')
        ctx.drawImage(img, 0, 0, w, h)
        const data = canvas.toDataURL('image/jpeg', 0.92)
        setSnapshot(data)
        // Mở modal sau khi đã có ảnh để tránh race-condition
        setEditorOpen(true)
        return
      } catch {
        // ignore and fallback to backend fetch
      }
    }

    // Nếu không thể chụp từ stream, vẫn mở modal (không có ảnh) để người dùng biết
    setEditorOpen(true)
  }, [rtsp])

  // Gắn sự kiện khi stream sẵn sàng để thử auto-detect một lần
  const onStreamLoad = useCallback(() => {
    // Thử ngay và nếu chưa thành công, thử lại trong vài nhịp (do MJPEG có thể chưa ổn định)
    let attempts = 0
    const maxAttempts = 10
    const tick = async () => {
      attempts += 1
      const ok = await tryAutoDetectFromStream()
      if (!ok && attempts < maxAttempts) setTimeout(tick, 200)
    }
    void tick()
  }, [tryAutoDetectFromStream])

  // Revoke blob URL when modal closes or component unmounts
  useEffect(() => {
    return () => {
      if (snapshot && snapshot.startsWith('blob:')) {
        try { URL.revokeObjectURL(snapshot) } catch {}
      }
    }
  }, [snapshot])

  // Xác định màu badge dựa trên mật độ
  const getDensityColor = (density: number) => {
    if (density === 0) return 'default'
    if (density <= 5) return 'success'
    if (density <= 15) return 'warning'
    return 'error'
  }

  // Xác định text mô tả mật độ
  const getDensityText = (density: number) => {
    if (density === 0) return 'Vắng'
    if (density <= 5) return 'Thưa'
    if (density <= 15) return 'Đông'
    return 'Rất đông'
  }

  return (
    <>
    <div className={`camera-tile ${focused ? 'focused' : ''}`} onDoubleClick={onDoubleClick} title="Nhấp đúp để phóng to/thu nhỏ" style={{ cursor: focused ? 'zoom-out' : 'zoom-in' }}>
      <div className="camera-stream" style={height ? { height } : undefined} ref={containerRef}>
        {ready && streamSrc ? (
          <img
            crossOrigin="anonymous"
            src={streamSrc}
            alt={name}
            style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
            onLoad={onStreamLoad}
          />
        ) : (
          <div className="camera-stream-inner">
            <div className="camera-stream-text">Chưa cấu hình stream</div>
          </div>
        )}

        {/* Hiển thị overlay vùng đã lưu (read-only) */}
        <RegionOverlay region={cameraRegion} toPixel={toPixel} readOnly />

        {ready && (
          <div className="edit-btn-overlay">
            <Tooltip title="Thiết lập vùng trên ảnh chụp">
              <Button size="small" icon={<EditOutlined />} onClick={takeSnapshot}>Bút</Button>
            </Tooltip>
          </div>
        )}
      </div>

      {/* Hiển thị mật độ phương tiện trên camera */}
      <div className="camera-density-overlay">
        <Tag color={getDensityColor(vehicleDensity)} style={{
          margin: 0,
          fontSize: '11px',
          fontWeight: 600,
          border: 'none',
          borderRadius: '4px'
        }}>
          {vehicleDensity} xe
        </Tag>
        <div className="density-text" style={{
          fontSize: '10px',
          color: 'rgba(255,255,255,0.8)',
          marginTop: '2px',
          textAlign: 'center'
        }}>
          {getDensityText(vehicleDensity)}
        </div>
      </div>

      <div className="camera-footer">
        <div className="camera-name">
          <Text>{name}</Text>
          {location && <Text type="secondary" style={{ marginLeft: 8 }}>• {location}</Text>}
        </div>
        <div>
          <Badge status={ready ? 'success' : 'default'} text={ready ? 'Ready' : 'Idle'} />
        </div>
      </div>
    </div>
    <RegionEditorModal open={editorOpen} cameraId={cameraId} imageSrc={snapshot} onClose={() => setEditorOpen(false)} rtsp={rtsp} />
    </>
  )
}
